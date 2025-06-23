import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from typing import Annotated

# Load environment variables
load_dotenv()
from pyngrok import ngrok
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp import ErrorData, McpError
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, TextContent
from mcp.server.auth.provider import AccessToken
from pydantic import AnyUrl, Field, BaseModel
import markdownify
import readabilipy


# --------------------- Configuration ---------------------
# Replace these with your actual values
AUTH_TOKEN = os.getenv("PUCH_AUTH_TOKEN")
MY_PHONE = os.getenv("MY_PHONE_NUMBER")  # Format: country_code + number (no +)

# Resume file path
RESUME_FOLDER = Path("./resume")
RESUME_FOLDER.mkdir(exist_ok=True)

# --------------------- Models ---------------------
class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None = None

# --------------------- Auth Provider ---------------------
class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        key = RSAKeyPair.generate()
        super().__init__(
            public_key=key.public_key, 
            jwks_uri=None, 
            issuer=None, 
            audience=None
        )
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token,
                client_id="puch-mcp-client",
                scopes=[],
                expires_at=None
            )
        return None

# --------------------- MCP Server Setup ---------------------
mcp = FastMCP("Puch AI MCP Server", auth=SimpleBearerAuthProvider(AUTH_TOKEN))

# --------------------- Resume Tool ---------------------
def find_resume_file() -> Path | None:
    """Find the resume file in the resume folder"""
    resume_extensions = ['.pdf', '.docx', '.doc', '.md', '.txt']
    for ext in resume_extensions:
        resume_files = list(RESUME_FOLDER.glob(f"*{ext}"))
        if resume_files:
            return resume_files[0]
    return None

def convert_resume_to_markdown(resume_path: Path) -> str:
    """Convert resume file to markdown format"""
    try:
        suffix = resume_path.suffix.lower()
        
        if suffix in [".md", ".txt"]:
            return resume_path.read_text(encoding='utf-8')
        
        elif suffix == ".pdf":
            try:
                import PyPDF2
                text = ""
                with open(resume_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                return text.strip()
            except ImportError:
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(resume_path)
                    text = ""
                    for page in doc:
                        text += page.get_text() + "\n"
                    doc.close()
                    return text.strip()
                except ImportError:
                    return "Error: Please install PyPDF2 or PyMuPDF to read PDF files"
        
        elif suffix in [".docx", ".doc"]:
            try:
                from docx import Document
                doc = Document(resume_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text.strip()
            except ImportError:
                return "Error: Please install python-docx to read Word documents"
        
        else:
            return f"Unsupported file type: {suffix}"
            
    except Exception as e:
        return f"Error reading resume: {str(e)}"

ResumeToolDescription = RichToolDescription(
    description="Serve your resume in plain markdown format",
    use_when="When Puch AI or anyone asks for your resume",
    side_effects=None
)

@mcp.tool(description=ResumeToolDescription.model_dump_json())
async def resume() -> str:
    """Return your resume in markdown format"""
    resume_path = find_resume_file()
    
    if not resume_path:
        return "Error: No resume file found in ./resume folder. Please add your resume file."
    
    markdown_content = convert_resume_to_markdown(resume_path)
    return markdown_content

# --------------------- Validation Tool ---------------------
@mcp.tool()
async def validate() -> str:
    """Validation tool required by Puch AI"""
    return MY_PHONE

# --------------------- Fetch Tool ---------------------
class Fetch:
    USER_AGENT = "Puch/1.0 (Autonomous)"
    
    @classmethod
    async def fetch_url(cls, url: str, force_raw: bool = False) -> tuple[str, str]:
        """Fetch URL and return content"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    follow_redirects=True,
                    headers={"User-Agent": cls.USER_AGENT},
                    timeout=30
                )
                
                if response.status_code >= 400:
                    raise McpError(
                        ErrorData(
                            code=INTERNAL_ERROR,
                            message=f"HTTP {response.status_code} error fetching {url}"
                        )
                    )
                
                content = response.text
                content_type = response.headers.get("content-type", "")
                
                is_html = "<html" in content.lower()[:100] or "text/html" in content_type
                
                if is_html and not force_raw:
                    return cls.extract_content_from_html(content), ""
                
                return content, f"Raw content (type: {content_type}):\n"
                
        except Exception as e:
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"Failed to fetch {url}: {str(e)}"
                )
            )
    
    @staticmethod
    def extract_content_from_html(html: str) -> str:
        """Extract content from HTML and convert to markdown"""
        try:
            result = readabilipy.simple_json.simple_json_from_html_string(
                html, use_readability=True
            )
            
            if not result.get("content"):
                return "<error>Failed to extract content from HTML</error>"
            
            markdown = markdownify.markdownify(
                result["content"],
                heading_style="ATX"
            )
            return markdown
            
        except Exception as e:
            return f"<error>Failed to process HTML: {str(e)}</error>"

FetchToolDescription = RichToolDescription(
    description="Fetch a URL and return its content in markdown format",
    use_when="When user provides a URL and wants its content",
    side_effects="Returns the content of the requested URL"
)

@mcp.tool(description=FetchToolDescription.model_dump_json())
async def fetch(
    url: Annotated[AnyUrl, Field(description="URL to fetch")],
    max_length: Annotated[int, Field(default=5000, description="Maximum characters to return")] = 5000,
    start_index: Annotated[int, Field(default=0, description="Starting character index")] = 0,
    raw: Annotated[bool, Field(default=False, description="Return raw HTML instead of markdown")] = False,
) -> list[TextContent]:
    """Fetch a URL and return its content"""
    
    if not url:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="URL is required"))
    
    url_str = str(url).strip()
    content, prefix = await Fetch.fetch_url(url_str, force_raw=raw)
    
    # Handle pagination
    original_length = len(content)
    if start_index >= original_length:
        content = "<error>No more content available</error>"
    else:
        content = content[start_index:start_index + max_length]
        
        if len(content) == max_length and (start_index + max_length) < original_length:
            next_start = start_index + max_length
            content += f"\n\n<info>Content truncated. Use start_index={next_start} to get more content.</info>"
    
    return [TextContent(type="text", text=f"{prefix}Content from {url}:\n{content}")]

# --------------------- Main Server Function ---------------------
async def main():
    """Start the MCP server"""
    print(f"🚀 Starting Puch AI MCP Server...")
    print(f"📄 Resume folder: {RESUME_FOLDER.absolute()}")
    
    resume_file = find_resume_file()
    if resume_file:
        print(f"📄 Found resume: {resume_file.name}")
    else:
        print("⚠️  No resume file found. Please add your resume to the ./resume folder")
    
    print(f"🔑 Auth token: {AUTH_TOKEN[:10]}...")
    print(f"📞 Phone number: {MY_PHONE}")
    print(f"🌐 Server will be available at: http://localhost:8085/mcp")
    print(f"🔌 To connect with Puch AI, use:")
    print(f"   /mcp connect <YOUR_PUBLIC_URL>/mcp {AUTH_TOKEN}")
    
    await mcp.run_async(transport="streamable-http")


# # Add this function before main()
# async def start_with_ngrok():
#     # Set your ngrok auth token
#     ngrok.set_auth_token("YOUR_NGROK_TOKEN")
    
#     # Start ngrok tunnel
#     public_url = ngrok.connect(8085)
#     print(f"🌐 Public URL: {public_url}")
#     print(f"🔌 Connect command: /mcp connect {public_url}/mcp {AUTH_TOKEN}")
    
#     # Start the server
#     await mcp.run_async("streamable-http", host="0.0.0.0", port=8085)




if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(main())