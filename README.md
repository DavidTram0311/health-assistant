# How to run

Step 1: 
```
git clone https://github.com/david0311-coder/health-coach-assistant
```
```
cd heath-coach-asssistant
```

Step 2:Install requirement dependencies
```
pip install -r requirements.txt
```

Step 3: Add Gemini API Key and TavilySearch API Key in `agent.py`:
```
os.environ['TAVILY_API_KEY'] = 'API_KEY'
os.environ["GOOGLE_API_KEY"] = 'API_KEY'
```

Step 4: run this cmd
```
pip install --upgrade "langgraph-cli[inmem]"
```

Step 5: 
```
langgraph dev
```