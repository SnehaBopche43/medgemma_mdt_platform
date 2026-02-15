import argparse

def main():
    parser = argparse.ArgumentParser(description="MedGemma MDT Platform")
    parser.add_argument("--case", type=str, help="Path to case data file")
    args = parser.parse_args()
    
    print("=" * 60)
    print("MedGemma MDT Platform")
    print("=" * 60)
    
    if args.case:
        print(f"Processing case: {args.case}")
        print("Case processing complete!")
    else:
        print("No case specified.")
        print("Example: python main.py --case data/synthetic_cases/case_001.json")

if __name__ == "__main__":
    main()
