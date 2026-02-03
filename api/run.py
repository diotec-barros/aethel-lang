#!/usr/bin/env python3
"""
Railway-compatible startup script
Reads PORT from environment variable correctly
"""
import os
import sys

def main():
    # Get port from environment, default to 8000
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Starting Aethel API on port {port}")
    
    # Import uvicorn
    import uvicorn
    
    # Run the app
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
