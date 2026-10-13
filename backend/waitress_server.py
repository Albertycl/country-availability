from waitress import serve
from main_testing_jenny_excel import create_app

app = create_app()

if __name__ == "__main__":
    serve(app, host='0.0.0.0', port=5030)