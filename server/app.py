"""
Server entry point for OpenEnv deployment
"""
from bom_normalizer.server import app

def main():
    """Main entry point for the server"""
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=7860)

if __name__ == '__main__':
    main()

__all__ = ['app', 'main']
