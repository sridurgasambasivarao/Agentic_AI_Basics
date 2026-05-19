In this project you'll build your first AI agent from scratch using Amazon Bedrock and AWS Lambda. By the end, you'll have a fully functional weather assistant that:

Understands natural language requests
Calls an external API to get real-time data
Synthesizes information into helpful responses

<img width="678" height="242" alt="image" src="https://github.com/user-attachments/assets/06921c36-6b07-491a-8e70-7ce9aba83d04" />

Understanding the lambda code:

* geocode_city: Converts city names to GPS coordinates
* get_grid_endpoints: Gets weather.gov forecast URLs for coordinates
* get_forecast: Fetches weather data
* summarize_hourly_24h: Formats data for easy reading
* lambda_handler: Main entry point that orchestrates everything

Try these queries:

- "What's the weather in NYC?"
- "How's the weather in Miami and New York?"
- "Is it going to rain in Boston today?"
- "What's the forecast for San Francisco?"
