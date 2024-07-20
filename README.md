# RAG 기반 챗봇 프로젝트

이 프로젝트는 RAG(Retrieval-Augmented Generation) 기반의 챗봇을 구현합니다. FastAPI를 사용하여 서버를 구축하고, Streamlit을 통해 사용자 인터페이스를 제공합니다.

## 프로젝트 아키텍처

```

project/
│
├── app/
│ ├── api/
│ │ └── v1/
│ │ ├── endpoints/
│ │ │ ├── **init**.py
│ │ │ └── chat.py
│ │ ├── **init**.py
│ ├── core/
│ │ └── config.py
│ ├── db/
│ │ ├── **init**.py
│ │ └── connection.py
│ ├── models/
│ │ └── **init**.py
│ ├── services/
│ │ ├── **init**.py
│ │ ├── embedding.py
│ │ ├── hwp_reader.py
│ │ └── vector_db.py
│ └── **init**.py
│ └── main.py
│
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── streamlit_app.py

```

### 각 파일 및 디렉토리 설명

1. **app/main.py**

   - FastAPI 애플리케이션의 엔트리 포인트입니다.
   - FastAPI 인스턴스를 생성하고 라우터를 포함시킵니다.

2. **app/api/v1/endpoints/chat.py**

   - API 엔드포인트가 정의된 파일입니다.
   - 사용자의 쿼리를 받아서 벡터 데이터베이스에서 검색한 결과를 반환합니다.

3. **app/core/config.py**

   - 설정 파일로, 환경 변수를 로드하고 설정값을 저장합니다.

4. **app/db/connection.py**

   - 데이터베이스 연결을 설정하는 파일입니다.
   - 현재는 비어 있지만, 필요에 따라 데이터베이스 연결 로직을 추가할 수 있습니다.

5. **app/models/**init**.py**

   - 모델 정의 파일입니다.
   - 현재는 비어 있지만, 추후 데이터베이스 모델을 추가할 수 있습니다.

6. **app/services/vector_db.py**

   - 벡터 데이터베이스 관련 로직을 처리하는 서비스 파일입니다.
   - 문서를 벡터로 변환하고 검색하는 기능을 포함합니다.

7. **app/services/embedding.py**

   - 텍스트를 벡터로 변환하는 함수가 포함된 파일입니다.

8. **app/services/hwp_reader.py**

   - HWP 파일을 읽고 텍스트를 추출하는 기능을 포함한 파일입니다.

9. **.env**

   - 환경 변수 파일입니다.
   - API 키와 같은 중요한 설정값을 저장합니다.

10. **requirements.txt**

    - 프로젝트의 종속성을 정의하는 파일입니다.

11. **streamlit_app.py**
    - Streamlit을 사용하여 사용자 인터페이스를 제공하는 파일입니다.

## 설치 및 실행 방법

### 1. 클론 및 환경 설정

```bash
git clone <repository-url>
cd project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음과 같이 설정합니다.

```makefile
OPENAI_API_KEY=your_openai_api_key
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### 3. FastAPI 서버 실행

```bash
uvicorn app.main:app --reload
```

### 4. Streamlit 인터페이스 실행

```bash
streamlit run streamlit_app.py
```

이제 브라우저에서 [http://127.0.0.1:8501](http://127.0.0.1:8501)로 이동하여 RAG 기반 챗봇을 사용할 수 있습니다.
