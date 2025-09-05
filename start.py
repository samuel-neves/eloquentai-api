Startup script for EloquentAI Backend
import uvicorn
import sys
import os

def main():
    print("🚀 Starting EloquentAI Backend...")

    try:
        uvicorn.run(
            "main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down EloquentAI Backend...")
    except Exception as e:
        
        sys.exit(1)

if __name__ == "__main__":
    main()
