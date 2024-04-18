from fastapi import FastAPI
from routers.first_page_module import router as first_page_router
from routers.second_page_module import router as second_page_router
from routers.third_page_module import router as third_page_router
import logging
from fastapi import FastAPI, status, HTTPException, Header, APIRouter
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(
      title="Streamlit Unified Survey Web Application API",
      summary="A collection of endpoints for Streamlit Unified Survey Web Application",
      version="0.1.0",
      docs_url="/docs",
      openapi_url="/openapi.json",
)

# @app.get("/", status_code=status.HTTP_200_OK)
# def root():
#     return {"message": "Welcome to the root of the FastAPI Survey Web Application!"}

@app.get("/", response_class=HTMLResponse, summary="Welcome_Page", tags= ["Root_Of_FastAPI_Application"])
def root():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Welcome to FastAPI Survey Web Application</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .container {
                text-align: center;
            }
            h1 {
                color: #333;
            }
            p {
                color: #666;
                font-size: 18px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to FastAPI Survey Web Application!</h1>
            <p>Thank you for visiting. This is the root of the application.</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


app.include_router(first_page_router, prefix="/first_page", tags=["Data_Cleaner_Pre_Processor"])
app.include_router(second_page_router, prefix="/second_page", tags=["Questionnaire_Definer"])
app.include_router(third_page_router, prefix="/third_page", tags=["Keypress_Decoder"])

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)