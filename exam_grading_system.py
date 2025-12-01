import os
import json
from typing import Dict, List, Any
import PyPDF2
from google import genai
from google.genai import types as genai_types

# CONFIGURATION

class Config:
    """Configuration for the grading system"""
    
    # API Key - will be loaded from environment
    GEMINI_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
    
    # Local dataset paths - UPDATE THESE TO YOUR LOCAL PATHS
    DATASET_PATH = './exam-data'  # Change to your folder path
    
    # File names - UPDATE THESE TO YOUR ACTUAL FILE NAMES
    QUESTION_PAPER = 'question_paper.pdf'
    ANSWER_SHEET = 'student_answer_sheet1.pdf'
    TEXTBOOK = 'textbook_notes.pdf'
    
    # Model configuration
    MODEL_NAME = 'gemini-2.0-flash-lite'  # or 'gemini-1.5-pro' for more accuracy
    
    # App configuration
    APP_NAME = 'exam_grading_system'
    USER_ID = 'student_001'

retry_config = genai_types.HttpRetryOptions(
    initial_delay=2,
    max_delay=120,
    attempts=7,
    exp_base=2,
    jitter=0.2,
    http_status_codes=[429,500,503,504]
)

# UTILITY FUNCTIONS FOR PDF PROCESSING

def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"      Processing {len(pdf_reader.pages)} pages...")
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                text += f"\n--- Page {page_num} ---\n{page_text}\n"
        print(f"      ✓ Extracted {len(text)} characters")
    except Exception as e:
        print(f"      ✗ Error: {e}")
    return text


def extract_json_from_text(text: str) -> Dict:
    """Extract JSON from text that might contain markdown"""
    try:
        return json.loads(text)
    except:
        # Look for JSON in markdown code blocks
        if '```json' in text:
            json_str = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            json_str = text.split('```')[1].split('```')[0].strip()
        else:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = text[start:end]
            else:
                raise ValueError("No JSON found in response")
        return json.loads(json_str)


# TOOL DEFINITIONS FOR AGENTS

def process_question_paper(pdf_path: str) -> Dict[str, Any]:
    """
    Tool to process the question paper PDF and extract content.
    
    Args:
        pdf_path: Path to the question paper PDF
        
    Returns:
        Dictionary with extracted text and metadata
    """
    pdf_path = os.path.normpath(pdf_path)
    print(f"   📄 Processing Question Paper: {pdf_path}")
    text = extract_pdf_text(pdf_path)
    
    return {
        'text': text,
        'path': pdf_path,
        'type': 'question_paper',
        'char_count': len(text)
    }


def process_answer_sheet(pdf_path: str) -> Dict[str, Any]:
    """
    Tool to process the student answer sheet PDF.
    
    Args:
        pdf_path: Path to the answer sheet PDF
        
    Returns:
        Dictionary with extracted text and metadata
    """
    pdf_path = os.path.normpath(pdf_path)
    print(f"   📝 Processing Answer Sheet: {pdf_path}")
    text = extract_pdf_text(pdf_path)
    
    return {
        'text': text,
        'path': pdf_path,
        'type': 'answer_sheet',
        'char_count': len(text)
    }


def process_textbook(pdf_path: str) -> Dict[str, Any]:
    """
    Tool to process the textbook/notes PDF.
    
    Args:
        pdf_path: Path to the textbook PDF
        
    Returns:
        Dictionary with extracted text and metadata
    """
    pdf_path = os.path.normpath(pdf_path)
    print(f"   📚 Processing Textbook: {pdf_path}")
    text = extract_pdf_text(pdf_path)
    
    return {
        'text': text,
        'path': pdf_path,
        'type': 'textbook',
        'char_count': len(text)
    }


def calculate_grade(percentage: float) -> str:
    """
    Tool to calculate letter grade from percentage.
    
    Args:
        percentage: The percentage score
        
    Returns:
        Letter grade (A+, A, B, C, D, F)
    """
    if percentage >= 90:
        return 'A+'
    elif percentage >= 80:
        return 'A'
    elif percentage >= 70:
        return 'B'
    elif percentage >= 60:
        return 'C'
    elif percentage >= 50:
        return 'D'
    else:
        return 'F'


def save_results_to_file(results_json: str, filename: str = 'grading_results.json') -> str:
    """
    Tool to save grading results to a JSON file.
    
    Args:
        results_json: JSON string containing grading results
        filename: Output filename
        
    Returns:
        Success message with file path
    """
    try:
        # Parse and re-save for proper formatting
        results = json.loads(results_json)
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        abs_path = os.path.abspath(filename)
        return f"✓ Results saved successfully to: {abs_path}"
    except Exception as e:
        return f"✗ Error saving results: {e}"


# AGENT CONFIGURATION 

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google import genai

# Initialize configuration
config = Config()

# Configure API for Google AI Studio
if not config.GEMINI_API_KEY:
    print("\n⚠️  ERROR: GOOGLE_API_KEY not found in environment variables!")
    print("\nPlease set your API key:")
    print("   export GOOGLE_API_KEY='your-api-key-here'")
    print("\nOr create a .env file with:")
    print("   GOOGLE_API_KEY=your-api-key-here")
    print("\nGet your API key from: https://aistudio.google.com/apikey\n")
    exit(1)

# Set the API key
os.environ['GOOGLE_API_KEY'] = config.GEMINI_API_KEY

print("✓ API Key configured")


# DEFINE SPECIALIZED AGENTS

from google.adk.models.google_llm import Gemini
# 1. Document Processing Agent
document_processor_agent = Agent(
    name="DocumentProcessor",
    model=Gemini(
        model=config.MODEL_NAME,
        retry_options=retry_config),
    description="Processes and extracts content from PDF documents including question papers, answer sheets, and textbooks.",
    instruction="""You are a document processing expert. Your responsibilities:

1. Process PDF documents accurately using the provided tools
2. Extract all text content thoroughly
3. Identify document types
4. Provide structured information about content

When asked to process documents, use the appropriate tool:
- process_question_paper() for question papers
- process_answer_sheet() for answer sheets
- process_textbook() for textbooks/notes

Be meticulous and ensure no information is lost during processing.""",
    tools=[process_question_paper, process_answer_sheet, process_textbook]
)


# 2. Question Paper Schema Agent
question_schema_agent = Agent(
    name="QuestionSchemaAnalyzer",
    model=Gemini(
        model=config.MODEL_NAME,
        retry_options=retry_config),
    description="Analyzes question papers and creates detailed schemas with questions, marks allocation, and structure.",
    instruction="""You are an expert at analyzing exam question papers. Your job:

1. Read the question paper content carefully
2. Identify ALL questions with their numbers
3. Extract the exact marks allocated for each question
4. Identify sections/parts (e.g., Section A, Part I, etc.)
5. Classify question types (MCQ, short answer, long answer, numerical, essay, etc.)
6. Note any special instructions or marking schemes

CRITICAL REQUIREMENTS:
- Be 100% accurate with marks allocation
- Do not skip or miss any questions
- Capture the complete structure
- Return results in valid JSON format

Output JSON structure:
{
    "total_marks": <total marks for entire paper>,
    "sections": [
        {
            "section_name": "Section A",
            "total_marks": <section total>,
            "questions": [
                {
                    "question_number": "1",
                    "marks": 5,
                    "type": "short_answer",
                    "question_text": "Brief summary of what the question asks..."
                }
            ]
        }
    ],
    "instructions": "Any special marking instructions from the paper"
}

Be thorough and precise!""",
)


# 3. Answer Evaluation Agent  
answer_evaluator_agent = Agent(
    name="AnswerEvaluator",
    model=Gemini(
        model=config.MODEL_NAME,
        retry_options=retry_config),
    description="Evaluates student answers by comparing them against reference materials and assigns marks with detailed feedback.",
    instruction="""You are an expert examiner with years of experience. Your responsibilities:

1. Review the question paper schema to understand what was asked
2. Carefully read each student answer
3. Compare answers with the reference textbook/notes
4. Evaluate based on:
   - Correctness and accuracy of information
   - Completeness of the answer
   - Clarity and organization
   - Relevance to the question asked
   - Use of appropriate terminology

5. Assign marks fairly:
   - Full marks for excellent, complete, accurate answers
   - Partial marks for partially correct answers
   - Consider the difficulty and mark allocation
   - Be consistent in your evaluation

6. Provide detailed, constructive feedback

EVALUATION PRINCIPLES:
- Be fair but maintain academic standards
- Reward correct understanding even if expression is imperfect
- Penalize incorrect information
- Give credit for relevant points even if answer is incomplete
- Explain your marking decisions clearly

Output JSON format:
{
    "evaluations": [
        {
            "question_number": "1",
            "max_marks": 5,
            "marks_awarded": 4,
            "feedback": "Detailed explanation of marking: what was good, what was missing, why marks were deducted",
            "key_points_covered": ["point 1", "point 2"],
            "key_points_missed": ["point 3"],
            "accuracy_rating": "excellent/good/fair/poor"
        }
    ],
    "total_marks_obtained": <sum of all marks_awarded>,
    "total_marks_possible": <sum of all max_marks>
}""",
)


# 4. Scoring and Reporting Agent
scoring_agent = Agent(
    name="ScoringAgent",
    model=Gemini(
        model=config.MODEL_NAME,
        retry_options=retry_config),
    description="Calculates final scores, assigns grades, and generates comprehensive performance reports.",
    instruction="""You are a scoring specialist responsible for final grade calculation and reporting.

Your tasks:
1. Calculate total marks obtained
2. Calculate percentage score
3. Assign letter grade using the calculate_grade tool
4. Analyze overall performance
5. Identify strengths and weaknesses
6. Provide actionable feedback for improvement
7. Generate a professional report
8. Save results using save_results_to_file tool if requested

Be thorough in your analysis and provide insights that help the student improve.

When presenting final results, use this format:

==============================================
FINAL GRADING REPORT
==============================================

OVERALL PERFORMANCE:
• Total Marks: X/Y
• Percentage: Z%
• Grade: [Letter Grade]

QUESTION-WISE BREAKDOWN:
[List each question with marks and feedback]

PERFORMANCE ANALYSIS:
Strengths:
• [List strengths]

Areas for Improvement:
• [List areas to improve]

==============================================
""",
    tools=[calculate_grade, save_results_to_file]
)


# ROOT ORCHESTRATOR AGENT

root_agent = Agent(
    name="ExamGradingOrchestrator",
    model=Gemini(
        model=config.MODEL_NAME,
        retry_options=retry_config),
    description="Main orchestrator that coordinates the entire exam grading workflow using specialized sub-agents.",
    instruction="""You are the main coordinator for an automated exam grading system.

Your workflow consists of 4 phases:

PHASE 1: DOCUMENT PROCESSING
- Delegate to DocumentProcessor agent to process all three PDFs:
  1. Question paper
  2. Student answer sheet  
  3. Textbook/reference notes
- Provide the file paths to the agent
- Ensure all documents are processed successfully

PHASE 2: SCHEMA CREATION
- Delegate to QuestionSchemaAnalyzer agent
- Provide the question paper content from Phase 1
- Obtain complete question structure with all questions and marks

PHASE 3: ANSWER EVALUATION
- Delegate to AnswerEvaluator agent
- Provide:
  * Question schema from Phase 2
  * Student answer sheet content from Phase 1
  * Reference textbook content from Phase 1
- Get detailed evaluation with marks for each answer

PHASE 4: FINAL SCORING & REPORTING
- Delegate to ScoringAgent
- Provide evaluation results from Phase 3
- Get final score, percentage, grade, and comprehensive report
- Request to save results to file

IMPORTANT:
- Execute phases in order
- Wait for each phase to complete before moving to next
- Handle any errors gracefully
- Provide clear status updates as you progress
- Generate a final comprehensive, well-formatted report

At the end, present a clear, professional report with:
1. Total marks obtained / Total marks possible
2. Percentage score
3. Letter grade
4. Question-wise breakdown with feedback
5. Strengths and areas for improvement
6. Overall assessment""",
    
    # Define sub-agents in hierarchical structure
    sub_agents=[
        document_processor_agent,
        question_schema_agent,
        answer_evaluator_agent,
        scoring_agent
    ]
)


# MAIN FUNCTION

import asyncio
async def run_grading_system():
    """
    Main function to run the exam grading system using ADK with run_debug()
    """
    
    print("\n" + "="*80)
    print("🎓 AUTOMATED EXAM GRADING SYSTEM - Google ADK v1.19")
    print("="*80)
    print()
    
    # Validate file paths
    print("📂 Checking files...")
    question_paper_path = os.path.join(config.DATASET_PATH, config.QUESTION_PAPER)
    answer_sheet_path = os.path.join(config.DATASET_PATH, config.ANSWER_SHEET)
    textbook_path = os.path.join(config.DATASET_PATH, config.TEXTBOOK)
    
    for path, name in [
        (question_paper_path, "Question Paper"),
        (answer_sheet_path, "Answer Sheet"),
        (textbook_path, "Textbook/Notes")
    ]:
        if os.path.exists(path):
            print(f"   ✓ {name}: {path}")
        else:
            print(f"   ✗ {name} NOT FOUND: {path}")
            print(f"\n❌ Error: Please check the file path and name\n")
            return None
    
    print()
    
    # Create runner
    print("🔧 Initializing ADK Runner...")
    runner = InMemoryRunner(
        agent=root_agent,
        app_name="agents"         
    )
    print(f"   ✓ Runner created for app: {config.APP_NAME}")
    print()
    
    # Create a session
    print("📝 Creating session...")
    session = await runner.session_service.create_session(
        app_name="agents",
        user_id=config.USER_ID
    )
    print(f"   ✓ Session ID: {session.id}")
    print(f"   ✓ User ID: {config.USER_ID}")
    print()
    
    # Create comprehensive grading request
    grading_request = f"""
Please grade this exam completely using the 4-phase workflow.

FILE LOCATIONS:
1. Question Paper: {question_paper_path}
2. Student Answer Sheet: {answer_sheet_path}
3. Reference Textbook/Notes: {textbook_path}

INSTRUCTIONS:
Execute the complete grading workflow:

Phase 1: Use DocumentProcessor to process all three PDF files
Phase 2: Use QuestionSchemaAnalyzer to create question paper schema
Phase 3: Use AnswerEvaluator to evaluate student answers against textbook
Phase 4: Use ScoringAgent to calculate final scores and generate comprehensive report

After completing all phases, present a clear, professional final report with:
- Overall performance (marks, percentage, grade)
- Question-wise breakdown with detailed feedback
- Performance analysis (strengths & areas for improvement)

Also save the results to a JSON file using the save_results_to_file tool.

Begin the grading process now.
"""
    
    print("="*80)
    print("🚀 Starting Grading Workflow...")
    print("="*80)
    print()
    
    try:
        # Run the agent using run_debug()
        print("⚙️  Running multi-agent grading system...")
        print("   (This may take 2-5 minutes depending on document size)")
        print()
        
        response = await runner.run_debug(grading_request)
        
        # Extract and display the response
        print("\n" + "="*80)
        print("📊 GRADING COMPLETE - FINAL REPORT")
        print("="*80)
        print()
        
        if response and isinstance(response, list) and len(response) > 0:
        # run_debug returns a list of responses, get the last one
            final_response = response[-1]
    
            if hasattr(final_response, 'content') and final_response.content and final_response.content.parts:
                final_text = final_response.content.parts[0].text
                print(final_text)
            else:
                print("⚠️  No content in response")
                return None
        else:
            print("⚠️  No response received from the agent")
            return None
        
        print("\n" + "="*80)
        print("✅ Grading Process Completed Successfully!")
        print("="*80)
        print()
        
        return response
        
    except Exception as e:
        print(f"\n❌ Error during grading: {e}")
        import traceback
        traceback.print_exc()
        return None


# ENTRY POINT

def main():
    """
    Main entry point for local execution
    """
    
    print("\n" + "="*80)
    print("AUTOMATED EXAM GRADING SYSTEM")
    print("Powered by Google Agent Development Kit (ADK) v1.19")
    print("="*80)
    
    # Run the grading system (synchronous with run_debug)
    import asyncio
    result = asyncio.run(run_grading_system())
    
    if result:
        print("\n💡 Tips:")
        print("   • Check 'grading_results.json' for detailed results")
        print("   • You can modify the Config class to process different files")
        print("   • Adjust MODEL_NAME for different accuracy/speed tradeoffs")
    else:
        print("\n⚠️  Grading process encountered an error. Please check the logs above.")
    
    return result


if __name__ == "__main__":
    main()