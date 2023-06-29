from typing import Any
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
from pdfquery import PDFQuery
from sentence_transformers import SentenceTransformer
import faiss
import pandas as pd
from typing_extensions import Annotated
import datetime
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)

model = SentenceTransformer('sentence-transformers/msmarco-MiniLM-L-6-v3')
embedding_length=384
number_of_results = 3


# we want storage to find the text, so we want vector -> text/document lookup too
# need way to deal with collisions between documents

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    fp = FileParser(file.filename, contents, file)
    file_text_list = fp.parse_file()

    db.insert_parsed_lines(file_text_list)
    print(db.df)
    return {"filename": file.filename}

@app.post("/text_upload")
async def search(text: Annotated[str, Form()],):
    fp = FileParser("text.txt", text)
    file_text_list = fp.parse_file()
    db.insert_parsed_lines(file_text_list)
    print(db.df)
    return {"message": "Text uploaded successfully!"}

@app.post("/search")
async def search(text: Annotated[str, Form()],):
    #results = db.lookup(text, k=number_of_results)
    oai = OpenAIInterface(text)
    oai.generate_semantic_query()
    oai.generate_lookup_results()
    summary = oai.get_open_ai()
    results = oai.get_query_results()
    return {"results": results, "summary":summary}


class OpenAIInterface:

    def __init__(self, _question) -> None:
        self.question = _question

    def generate_semantic_query(self):
        query = "We are a semantic search algorithm. Generate a list of unique related keywords including relevent information from the prompt " + \
        "related to the following user question: '" + self.question + "'\nDo not use invalid characters for a python eval. Return a list of 5 keywords in the following EXACT format:" + \
        "\n['realated semantic question', 'realated semantic question','realated semantic question','realated semantic" + \
        "question','realated semantic question']\n"
        chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "system", "content": query}])
        searches = chat_completion.get("choices")[0].get("message").get("content")
        searches = eval(searches)
        print(searches)
        self.queries = searches
    
    def generate_lookup_results(self):
        all_results = []
        for query in self.queries:
            current_results = db.lookup(query, k=number_of_results)
            all_results += current_results
        self.results = all_results
    
    def get_query_results(self):
        return self.results

    def get_open_ai(self):
        query = "We are a semantic search algorithm. Given the following user question:\n'" + self.question + \
            "\n'and the following semantic search results from a set of preloaded documents:\n'" + \
            self.get_result_text() + "'\nReturn a summary of the search results that best answers" + \
            " the user question above. Do not include prompt context or mention any search results." + \
            " Just write a summary that answers the question combining information from the documents given:\n"
        print(query)
        chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "system", "content": query}])
        return chat_completion.get("choices")[0].get("message").get("content")

    def get_result_text(self):
        result_string = ''
        for result in self.results:
            new_string = "\nFile: " + str(result[0]) + "\nText: " + str(result[1])
            if len(result_string) + len(new_string) > 3000:
                return result_string
            else:
                result_string += new_string
        return result_string


class FileParser:

    def __init__(self, _file_name, _raw_file_content, _raw_file) -> None:
        self.raw_file = _raw_file
        self.file_name = _file_name
        self.file_type = _file_name.split(".")[-1]
        self.raw_file_content = _raw_file_content

    def parse_file(self):
        raw_text = []
        if self.file_type == "html":
            raw_text = self.parse_html()
        elif self.file_type == "txt":
            raw_text = self.parse_text()
        else:
            raw_text = self.parse_pdf()

        return self.merge_lines(raw_text)
    
    def merge_lines(self, raw_text):
        raw_text = self.apply_string_min_length(raw_text)
        raw_text = self.apply_string_max_length(raw_text)
        #raw_text = self.overlap_strings(raw_text)
        new_string_list = []
        for raw_row in raw_text:
            new_string_list.append((raw_row[0], " ".join(raw_row[1]), raw_row[2]))
        return new_string_list
    
    def overlap_strings(self, strings):
        overlapped_strings = []

        for i in range(len(strings) - 1):
            current_string = strings[i][1]
            overlap_length = len(current_string) // 2
            overlapped_string = current_string[:overlap_length] + strings[i + 1][1][overlap_length:]
            overlapped_strings.append((strings[i][0], overlapped_string, str(strings[i][2].split("-")[0])+"-"+str(strings[i+1][2].split("-")[-1])))
        
        all_string_list = overlapped_strings + strings
        return all_string_list


    def apply_string_max_length(self, strings, threshold=500):
        new_strings = []
        for current_row in strings:
            string = current_row[1]
            if len(string) <= threshold:
                new_strings.append(current_row)
            else:
                while len(string) > threshold:
                    new_strings.append((current_row[0], string[:threshold], current_row[2]))
                    string = string[threshold:]
                    
                if len(string) > 0:
                    new_strings.append((current_row[0], string, current_row[2]))
        return new_strings


    def apply_string_min_length(self, raw_text):
        initial_number_of_strings = len(raw_text)
        new_string_list = []
        new_string = []
        start_line = raw_text[0][2]
        current_doc = raw_text[0][0]
        count = 0
        while count < initial_number_of_strings:
            new_string += raw_text[count][1].split(" ")
            if len(new_string) > 100:
                new_string_list.append((current_doc, new_string, str(start_line)+"-"+str(raw_text[count][2])))
                start_line = raw_text[count][2]
                new_string = []
            count+=1
        return new_string_list


    def parse_text(self):
        return [("text_input"+str(datetime.datetime.now()), self.raw_file_content, 0)]

    def parse_html(self):
        soup = BeautifulSoup(self.raw_file_content, 'html.parser')
        text_list = []

        def process_element(element):
            if element.string and element.string.strip():  # Check if the element has non-empty text
                text = element.string.strip()
                line_reference = element.sourceline
                text_with_line = (self.file_name, text, line_reference)
                text_list.append(text_with_line)

            for child in element.children:
                if child.name:  # Check if the child is a tag
                    process_element(child)

        process_element(soup)
        return text_list

    def parse_pdf(self):
        pdf = PDFQuery(self.raw_file.file)
        pdf.load()

        text_elements = pdf.pq('LTTextLineHorizontal')
        text_elements_indexed = []
        for i, element in enumerate(text_elements):
            if element.text != '' and (len(element.text) > 6 and len(element.text.split(" ")) > 2):
               text_elements_indexed.append((self.file_name,element.text,i))
        return text_elements_indexed

class VectorDB:

    def __init__(self):
        self.index = faiss.IndexFlatL2(384)
        self.init_df_lookup()

    def init_df_lookup(self):
        self.df = pd.DataFrame(columns=['DatasetName', 'text', 'line'])
    
    def insert_parsed_lines(self, parsed_lines):
        for line_value in parsed_lines:
            self.insert_line(line_value[0], line_value[1], line_value[2])


    def insert_line(self, dataset_name, text, line_number):
        """ Inserts value into pandas df and faiss at the same index """
        index = self.df.shape[0]
        self.df.loc[index] = [dataset_name, text, line_number]
        vector = self.get_vector(text)
        self.index.add(vector)

    def lookup(self, text, k=1):
        """ Performs a k-nearest neighbor search using faiss """
        vector = self.get_vector(text)
        _, indices = self.index.search(vector, k)
        results = []
        try:
            for i in indices[0]:
                result = self.df.loc[i]
                results.append([str(result['DatasetName']), str(result['text']), str(result['line'])])
        except:
            results = ["None"]
        return results

    def get_vector(self, text):
        embeddings = model.encode([text])
        faiss.normalize_L2(embeddings)
        return embeddings

db = VectorDB()


