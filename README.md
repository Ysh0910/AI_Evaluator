# Automated Exam Grading System

An intelligent exam grading system that leverages Google's Generative AI (Gemini) and the Google Agent Development Kit (ADK) to automatically grade student exam papers.

## Features

- **Automated Grading**: Uses Gemini AI to grade student answers against question papers
- **PDF Processing**: Extracts and processes PDF files for questions, answers, and reference materials
- **Intelligent Analysis**: Compares student responses with textbook notes and model answers
- **Detailed Reports**: Generates comprehensive grading reports with feedback

## Prerequisites

Before running this project, ensure you have:

- **Python 3.10+** installed on your system
- **Google API Key** from [Google AI Studio](https://aistudio.google.com/apikey)
- **pip** (Python package manager)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Ysh0910/AI_Evaluator
cd Evaluator
```

### 2. Create a Virtual Environment (Recommended)
```bash
# On Windows
python -m venv grading_env
grading_env\Scripts\activate

# On macOS/Linux
python -m venv grading_env
source grading_env/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up API Key

Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your-api-key-here
```

Alternatively, set the environment variable:
```bash
# On Windows (PowerShell)
$env:GOOGLE_API_KEY = "your-api-key-here"

# On macOS/Linux
export GOOGLE_API_KEY="your-api-key-here"
```

## Usage

### 1. Prepare Your Exam Files

Place your exam PDF files in the `exam-data/` folder:
- `question_paper.pdf` - The exam questions
- `student_answer_sheet1.pdf` - Student's answers
- `textbook_notes.pdf` - Reference material for grading

### 2. Update Configuration

Edit `exam_grading_system.py` and update the `Config` class if your file names differ:
```python
DATASET_PATH = './exam-data'  # Path to your exam files
QUESTION_PAPER = 'question_paper.pdf'
ANSWER_SHEET = 'student_answer_sheet1.pdf'
TEXTBOOK = 'textbook_notes.pdf'
```

### 3. Run the Grading System
```bash
python exam_grading_system.py
```

The system will process the files and output grading results.

## Configuration

The `Config` class in `exam_grading_system.py` allows you to customize:

- **MODEL_NAME**: Choose between `gemini-2.0-flash-lite` or `gemini-1.5-pro`
- **DATASET_PATH**: Directory containing your exam files
- **Retry Configuration**: Adjust API retry settings if needed

## Project Structure

```
Evaluator/
├── exam_grading_system.py    # Main application
├── exam-data/                # Folder for PDF files
│   ├── question_paper.pdf
│   ├── student_answer_sheet1.pdf
│   └── textbook_notes.pdf
├── grading_env/              # Virtual environment (auto-created)
├── README.md                 # This file
├── .gitignore               # Git ignore rules
└── requirements.txt         # Python dependencies
```

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'google'"**
   - Solution: Install dependencies: `pip install -r requirements.txt`

2. **"GOOGLE_API_KEY not found"**
   - Solution: Ensure your `.env` file is created and contains the correct API key

3. **"PDF file not found"**
   - Solution: Check that exam files are in the `exam-data/` folder and file names match the Config

4. **API Rate Limiting**
   - Solution: The system includes automatic retry logic with exponential backoff

## Technologies Used

- **Python 3.10+**
- **Google Generative AI (Gemini)** - For intelligent grading
- **Google Agent Development Kit (ADK)** - For agentic capabilities
- **PyPDF2** - For PDF processing
- **python-dotenv** - For environment variable management

## Dependencies

See `requirements.txt` for a complete list of dependencies. Key packages:
- google-adk (≥1.19.0)
- google-generativeai
- PyPDF2
- python-dotenv
- fastapi
- uvicorn

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the [Google AI Documentation](https://ai.google.dev/)
3. Open an issue on GitHub

## Disclaimer

This system is designed for educational purposes. Always review AI-generated grades with human judgment, especially for high-stakes assessments.
