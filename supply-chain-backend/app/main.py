from fastapi import FastAPI

app = FastAPI(title="Supply Chain Time Cycle & Bottleneck Analyzer")


@app.get("/")
def root():
    return {"message": "Supply Chain API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}