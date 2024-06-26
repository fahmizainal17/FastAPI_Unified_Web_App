from pathlib import Path
import pytest
import pandas as pd
from io import BytesIO
import json
from tests.test_main import app
from tests.routers.test_first_page_module import merger, process_file, FileProcessRequest
from tests.routers.test_second_page_module import parse_questions_and_answers, parse_text_to_json, rename_columns ,Questionnaire
from tests.routers.test_third_page_module import parse_text_to_json_third_page, custom_sort, classify_income, process_file_content, flatten_json_structure
from fastapi import UploadFile
from starlette.datastructures import UploadFile
from fastapi.datastructures import UploadFile
from typing import Any
from pydantic import BaseModel

# ---------------------------------------------------
# Connection Test
# ---------------------------------------------------

@app.get("/")
def read_main():
    return {"message": "Welcome to the Unit Testing"}

# ---------------------------------------------------s
# First Page Module Tests
# ---------------------------------------------------

@pytest.fixture
def create_data():
    """Fixture to create DataFrame input for testing."""
    data = [
        {"PhoneNo": "1234567890", "UserKeyPress": "FlowNo_2=1"},
        {"PhoneNo": "0987654321", "UserKeyPress": "FlowNo_2=2"}
    ]
    return pd.DataFrame(data)

def test_merger(create_data: pd.DataFrame):
    df_list = [create_data]
    phonenum_list = [create_data[['PhoneNo']]]
    df_merge, phonenum_combined = merger(df_list, phonenum_list)
    
    assert not df_merge.empty
    assert 'PhoneNo' in df_merge.columns
    assert not phonenum_combined.empty
    assert 'phonenum' in phonenum_combined.columns

def test_process_file(create_data: pd.DataFrame):
    df_json = create_data.to_json(orient='records')
    request = FileProcessRequest(df_json=df_json)  # Creating a Pydantic model instance
    result = process_file(request)  # Directly invoking the function with the correct input

    assert 'df_complete' in result
    assert len(result['df_complete']) == 2  # Expecting 2 entries after processing
    assert result['total_calls'] == 2
    assert result['total_pickup'] == 2
    assert 'df_merge' in result
    assert len(result['df_merge']) > 0  # Ensuring df_merge is not empty

# ---------------------------------------------------
# Second Page Module Tests
# ---------------------------------------------------

@pytest.fixture
def json_data_input():
    data = {
        "questions": {
            "Q1": {
                "question": "What is your favorite fruit?",
                "answers": {
                    "FlowNo_2=1": "Apple",
                    "FlowNo_2=2": "Banana"
                }
            },
            "Q2": {
                "question": "What is your favorite color?",
                "answers": {
                    "FlowNo_3=1": "Blue",
                    "FlowNo_3=2": "Red",
                    "FlowNo_3=3": "Green"
                }
            }
        }
    }
    return UploadFile(file=BytesIO(json.dumps(data).encode('utf-8')), filename="test.json")

@pytest.fixture
def text_content_input():
    content = (
        "1. What is your favorite fruit?\n"
        "   - Apple\n"
        "   - Banana\n\n"
        "2. What is your favorite color?\n"
        "   - Blue\n"
        "   - Red\n"
        "   - Green"
    )
    return UploadFile(file=BytesIO(content.encode('utf-8')), filename="test.txt")

def test_parse_questions_and_answers(json_data_input: UploadFile):
    json_data_input.file.seek(0)  # Rewind the file to the start
    data = json.load(json_data_input.file)  # Reading and decoding JSON data correctly
    questionnaire = Questionnaire(**data)  # Create a Pydantic model instance with the loaded data
    parsed_data = parse_questions_and_answers(questionnaire)  # Pass the Pydantic model to the function
    assert isinstance(parsed_data, dict)
    assert 'Q1' in parsed_data and 'Q2' in parsed_data
    assert parsed_data['Q1']['answers']['FlowNo_2=1'] == "Apple"
    assert parsed_data['Q2']['answers']['FlowNo_3=1'] == "Blue"

class TextContent(BaseModel):
    text_content: str

def test_parse_text_to_json():
    # Simulate the JSON input as it would be received from an API call
    text_content = (
        "1. What is your favorite fruit?\n"
        "   - Apple\n"
        "   - Banana\n\n"
        "2. What is your favorite color?\n"
        "   - Blue\n"
        "   - Red\n"
    )
    input_data = TextContent(text_content=text_content)
    parsed_data = parse_text_to_json(input_data)

    # Now assert based on the expected results
    assert "Q1" in parsed_data and "Q2" in parsed_data
    assert parsed_data["Q1"]["answers"]["FlowNo_2=1"] == "Apple"
    assert parsed_data["Q2"]["answers"]["FlowNo_3=1"] == "Blue"

# Define the Pydantic model for the test, if not already defined
class RenameColumnsRequest(BaseModel):
    columns: list
    data: list
    new_column_names: list

def test_rename_columns(create_data: pd.DataFrame):
    request = RenameColumnsRequest(
        columns=create_data.columns.tolist(),
        data=create_data.values.tolist(),
        new_column_names=['PhoneNumber', 'UserAction']
    )
    # Since `rename_columns` returns a list of dictionaries
    result = rename_columns(request)
    # Check if the new column names are present in each dictionary of the list
    assert all('PhoneNumber' in row and 'UserAction' in row for row in result), "New column names not found in all rows"

# ---------------------------------------------------
# Third Page Module Tests
# ---------------------------------------------------

class TextContent(BaseModel):
    text_content: str

def test_parse_text_to_json_third_page(text_content_input: UploadFile):
    text_content_input.file.seek(0)
    content = text_content_input.file.read().decode('utf-8')
    request = TextContent(text_content=content)
    result = parse_text_to_json_third_page(request)
    assert "Q1" in result and "Q2" in result
    assert result["Q1"]["answers"]["FlowNo_2=1"] == "Apple"
    assert result["Q2"]["answers"]["FlowNo_3=1"] == "Blue"

def test_custom_sort():
    result = custom_sort("FlowNo_2=3")
    assert result == {"question_num": 2, "flow_no": 3}

def test_classify_income():
    assert classify_income("RM4,850 & below") == {"income_group": "B40"}
    assert classify_income("RM10,961 to RM15,039") == {"income_group": "T20"}

@pytest.fixture
def flow_no_mappings_input():
    return {
        "Q1": {
            "question": "Did you vote in the Petaling Jaya Parliament?",
            "answers": {
                "FlowNo_2=1": "Yes",
                "FlowNo_2=2": "No"
            }
        }
    }

@pytest.fixture
def json_file_input(tmp_path: Path):
    data = '{"Q1": {"question": "Did you vote in the Petaling Jaya Parliament?", "answers": {"FlowNo_2=1": "Yes", "FlowNo_2=2": "No"}}}'
    file_path = tmp_path / "test.json"
    file_path.write_text(data, encoding='utf-8')
    return str(file_path)

def test_process_file_content_json(json_file_input: str):
    content_type = "application/json"
    result, message, error = process_file_content(json_file_input, content_type)
    expected_message = "Questions and answers parsed successfully.✨"
    assert message.strip() == expected_message
    assert "Q1" in result
    assert result['Q1']['answers']['FlowNo_2=1'] == "Yes"
    assert error is None

@pytest.fixture
def text_file_input(tmp_path: Path):
    content = "1. What is your favorite sport?\n   - Soccer\n   - Basketball\n2. What is your favorite color?\n   - Blue\n   - Red\n   - Green"
    file_path = tmp_path / "test.txt"
    file_path.write_text(content, encoding='utf-8')
    return str(file_path)

def test_process_file_content_text(text_file_input: str):
    content_type = "text/plain"
    result, message, error = process_file_content(text_file_input, content_type)
    expected_message = "Questions and answers parsed successfully.✨"
    assert message == expected_message
    assert 'flow_no_mappings' in result
    assert "Q1" in result['flow_no_mappings']
    assert result['flow_no_mappings']['Q1']['answers']['FlowNo_1'] == "Soccer"

@pytest.fixture
def flow_no_mappings_input():
    return {
        "Q1": {
            "question": "What is your favorite hobby?",
            "answers": {
                "FlowNo_2=1": "Reading",
                "FlowNo_2=2": "Writing"
            }
        }
    }

def test_flatten_json_structure(flow_no_mappings_input: dict):
    # Wrap the input in the 'flow_no_mappings' key
    wrapped_input = {"flow_no_mappings": flow_no_mappings_input}
    
    result = flatten_json_structure(wrapped_input)
    assert "FlowNo_2=1" in result, "Key 'FlowNo_2=1' not found in the result."
    assert result["FlowNo_2=1"] == "Reading", f"Expected 'Reading', got {result.get('FlowNo_2=1')}"

# ---------------------------------------------------
# Running Pytest Directly
# ---------------------------------------------------

if __name__ == "__main__":
    pytest.main()
