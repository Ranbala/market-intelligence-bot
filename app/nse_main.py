from database import init_db
from main import run_nse_filing_pipeline

if __name__ == "__main__":

    init_db()

    run_nse_filing_pipeline()