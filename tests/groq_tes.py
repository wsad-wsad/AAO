from groq import Groq

client = Groq()
completion = client.chat.completions.create(
    model="qwen/qwen3-32b",
    messages=[
        {
            "role": "system",
            "content": "Anda adalah asisten yang membantu menghasilkan data JSON.",
        },
        {
            "role": "assistant",
            "content": "Buatkan saya objek **json** yang mendeskripsikan apa itu python.",
        },
    ],
    temperature=0.6,
    max_completion_tokens=8020,
    top_p=0.95,
    reasoning_effort="default",
    stream=False,
    response_format={"type": "json_object"},
    stop=None,
)

print(completion.choices[0].message)
