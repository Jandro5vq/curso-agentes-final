import sqlite3
import json
from pathlib import Path

db_path = Path('./data/news_state.db')
print(f"Base de datos: {db_path.absolute()}")
print(f"Existe: {db_path.exists()}")

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Listar tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\n=== TABLAS: {[t[0] for t in tables]} ===\n")
    
    # Revisar daily_states
    cursor.execute("SELECT COUNT(*) FROM daily_states")
    count = cursor.fetchone()[0]
    print(f"daily_states: {count} registros")
    
    if count > 0:
        cursor.execute("SELECT * FROM daily_states ORDER BY date DESC LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f"\n  === REGISTRO ===")
            print(f"  chat_id: {row['chat_id']}, date: {row['date']}")
            state = json.loads(row['state_json'])
            print(f"  keys: {list(state.keys())}")
            print(f"  mode: {state.get('mode')}")
            print(f"  user_input: {state.get('user_input')}")
            print(f"  articles: {len(state.get('articles', []))} artículos")
            print(f"  audio_path: {state.get('audio_path')}")
            
            if state.get('answer'):
                print(f"  answer: {state.get('answer')[:200]}...")
            
            if state.get('script'):
                print(f"\n  === SCRIPT GENERADO ({len(state.get('script').split())} palabras) ===")
                print(f"  {state.get('script')[:800]}...")
            
            if state.get('articles'):
                print(f"\n  === ARTÍCULOS ===")
                for i, art in enumerate(state.get('articles', [])[:3]):
                    if isinstance(art, dict):
                        print(f"    {i+1}. {art.get('title', 'Sin título')[:60]}...")
                    else:
                        print(f"    {i+1}. {str(art)[:60]}...")
    
    # Revisar conversation_history
    cursor.execute("SELECT COUNT(*) FROM conversation_history")
    count = cursor.fetchone()[0]
    print(f"\n\n=== CONVERSATION_HISTORY: {count} registros ===")
    
    if count > 0:
        cursor.execute("SELECT * FROM conversation_history ORDER BY created_at DESC LIMIT 10")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  - chat_id: {row['chat_id']}, role: {row['role']}, date: {row['date']}, created_at: {row['created_at']}")
            content_preview = row['content'][:150] if len(row['content']) > 150 else row['content']
            print(f"    content: {content_preview}")
    
    conn.close()
else:
    print("La base de datos no existe!")
