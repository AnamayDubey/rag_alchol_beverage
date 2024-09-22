import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.messages import HumanMessage
from PIL import Image
import base64
from io import BytesIO
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set your Google API key
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
if not os.environ["GOOGLE_API_KEY"]:
    logging.error("GOOGLE_API_KEY not found in environment variables.")
    raise ValueError("GOOGLE_API_KEY is not set")

# Initialize the Gemini Pro Vision model
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1)

def encode_image(image_path):
    with Image.open(image_path) as img:
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

def analyze_image(image_path):
    logging.info(f"Analyzing image: {image_path}")
    # Encode the image
    base64_image = encode_image(image_path)
    
    system_prompt = '''
        You are an AI assistant specialized in analyzing charts and trends from PowerPoint slides about alcoholic beverages. 
        Provide a detailed and accurate description of the image, focusing on the data presented, trends observed, and any key insights. 
        Do not fabricate or hallucinate information not present in the image.
    '''
    
    user_prompt = '''
        Analyze the following image of a PowerPoint slide containing charts and trends related to alcoholic beverages. 
        Describe what you see in detail, including the type of chart, data presented, trends, and any important insights. 
        Be specific and accurate, and do not include any information that is not visible in the image.
    '''
    
    # Create the prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt)
    ])
    
    # Format the prompt with the image
    formatted_messages = prompt.format_messages(
        image=f"data:image/jpeg;base64,{base64_image}"
    )
    
    # Add the image to the last message (which should be the HumanMessage)
    if isinstance(formatted_messages[-1].content, str):
        formatted_messages[-1].content = [
            {"type": "text", "text": formatted_messages[-1].content},
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"}
        ]
    else:
        formatted_messages[-1].content.append(
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"}
        )
    
    # Generate the response
    try:
        response = model.invoke(formatted_messages)
        logging.info("Successfully generated description")
        return response.content
    except Exception as e:
        logging.error(f"Error generating description: {str(e)}")
        raise

def process_images(input_folder, output_folder):
    logging.info(f"Processing images from {input_folder}")
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all jpg files from the input folder
    image_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.jpg')]
    
    for i, image_file in enumerate(image_files, start=1):
        image_path = os.path.join(input_folder, image_file)
        try:
            description = analyze_image(image_path)
            
            # Write the description to a text file
            output_file = os.path.join(output_folder, f"slide_{i}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(description)
            
            logging.info(f"Processed {image_file} - Description saved to {output_file}")
        except Exception as e:
            logging.error(f"Error processing {image_file}: {str(e)}")

# Example usage
input_folder = "alcoholic-beverage"
output_folder = "descriptions"
process_images(input_folder, output_folder)