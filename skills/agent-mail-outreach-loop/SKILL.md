---
name: agentmail-outreach-loop
description: End-to-end automated cold email pipeline: lead scraping, HTML demo generation, and AgentMail email blasting with background polling.
---

# AgentMail Cold Outreach Loop

When tasked with running a cold email outreach campaign (e.g., for selling web design to restaurants), execute the following pipeline:

## 1. Scrape & Source Leads
Use the `search_web` tool to find target businesses that have a public email address. Gather their name, email, and specific details.

## 2. Generate Custom Artifacts (Demos)
Write a Node or Python script to dynamically generate a custom artifact (like a personalized HTML mockup) for each lead and save it locally.

## 3. Draft Eye-Catching Hooks (CRITICAL)
Do NOT use generic openers like "Hey team, your food looks incredible." 
Instead, draft aggressive, eye-catching, and highly personalized hooks that immediately grab attention. Focus on the money they are losing by not having a modern digital presence.
*Example:* "Your IG is blowing up, but your lack of a website is costing you 50+ local Google Search customers every single week."

## 4. Blast via AgentMail
Use a Node.js script with the `agentmail` and `agentmail-toolkit` packages to send the batch.
**Technical Constraints to remember:**
- The `send_message` tool requires `to` to be an array of strings: `to: ["target@gmail.com"]`.
- The inbox parameter is camelCase: `inboxId: "your-inbox@agentmail.to"`.

## 5. Background Polling
Because AgentMail does not push real-time webhooks locally, use the `schedule` tool to set up a recurring cron job (e.g., `*/10 * * * *`) that executes a background Node script. The script should use `client.threads.list('your-inbox@agentmail.to')` to check for replies and silently exit if the count is 0.
