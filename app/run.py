import os
import random
import time
from langfuse.decorators import observe, langfuse_context
from langfuse import Langfuse

# API Credentials
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-f35359ec-7fbc-46de-a2bf-faf811998739" 
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-27c5206b-24db-4776-aee9-cd95c0b799fd"
os.environ["LANGFUSE_HOST"] = "https://cloud.langfuse.com"

langfuse = Langfuse()

@observe()
def call_fake_llm(user_query):
    # Get the ID of the current trace managed by the decorator
    trace_id = langfuse_context.get_current_trace_id()
    
    # Use the main langfuse client to create a generation linked to this trace
    generation = langfuse.generation(
        trace_id=trace_id,
        name="gpt-4-mock",
        model="gpt-4",
        input=[{"role": "user", "content": user_query}],
        metadata={"env": "production"}
    )
    
    time.sleep(random.uniform(0.5, 1.0))
    output = f"Fake response for: {user_query}"
    
    # End the generation with tokens to ensure costs appear
    generation.end(
        output=output,
        usage={
            "prompt_tokens": random.randint(50, 100),
            "completion_tokens": random.randint(100, 200)
        }
    )
    return output

@observe()
def run_full_trace(trace_index):
    langfuse_context.update_current_trace(
        name=f"Full-Demo-Trace-{trace_index}",
        user_id=f"user_vinuni_{random.randint(1, 5)}",
        tags=["simulated", "v2.60"]
    )
    
    result = call_fake_llm("Explain quantum physics simply.")
    
    # Add a score
    langfuse.score(
        trace_id=langfuse_context.get_current_trace_id(),
        name="user-satisfaction",
        value=random.uniform(0.8, 1.0)
    )
    return result

if __name__ == "__main__":
    if langfuse.auth_check():
        print("🚀 Pushing 5 full traces...")
        for i in range(5):
            print(f"  - Sending trace {i+1}/5")
            run_full_trace(i)
        
        langfuse.flush()
        print("✅ Done! Check your dashboard.")
    else:
        print("❌ Auth failed.")