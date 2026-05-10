# Portal-Router: Automated Triage Classification for Patient Inquiries

Presentation Slides: https://canva.link/my43x7a1slxsfkf 
Live Interactive Deployment: https://hospital-router-app.streamlit.app/


---

## 1. Context (and Personal Motivation), User, and Problem
As a Graduate Research Assistant at the Johns Hopkins University Center for Digital Health and AI, my work focuses on developing technical solutions to real-world healthcare challenges. The inspiration for this project comes from a deeply personal frustration with the current state of digital healthcare. I have experienced firsthand the frustration of using patient portals where messages seem to disappear into the system. Often, patients wait days for a response simply because their inquiry was routed to the wrong department, such as a billing question being sent to a clinical nurse. This application was built to eliminate that bottleneck by using semantic intelligence to ensure every patient message reaches the correct care team member immediately. We are told that patient portals are supposed to act as direct bridges to our care teams. Still, in reality, they often function like administrative bottlenecks where urgent messages just get completely lost in the sauce. 

To understand the problem, imagine a patient who has just undergone surgery and is experiencing unexpected side effects. They log into their MyChart portal and type a panicked, conversational message: "I've been feeling incredibly dizzy since I started taking the new medication, and I need to know if my Blue Cross insurance covers an emergency checkup." In a traditional hospital workflow, this unstructured text hits a bottleneck where a legacy keyword filter might spot the word "insurance" and automatically route this urgent clinical symptom straight to the billing department's queue. That ticket might sit in the wrong inbox for days, entirely unseen by a doctor.

This brings us to the target users for this project: Hospital Patient Experience Coordinators and Helpdesk Agents. These staff members are currently drowning in inbox clutter, forced to spend hours every day manually reading and rerouting unstructured patient inquiries. When they have to play middleman, specialized nurses waste their own time fixing administrative errors, and patients are left waiting in the dark for answers.

By using high-speed semantic intelligence, the system evaluates the true intent behind a patient's free-text message and automatically classifies it into one of four specific departments: Billing, Scheduling, Clinical, or IT Support. It then generates the precise Oracle SQL statement needed to route the ticket, allowing the human triage agent to review the AI's recommendation and securely commit it to the hospital's database with a single click. Automating this triage workflow reduces response latency, saves significant administrative overhead, and most importantly, ensures that a patient's medical concern reaches a clinical professional immediately—not an IT tech or a billing coordinator.

Overview Summary:
* **Target User**: Hospital Patient Experience Coordinators and Helpdesk Agents.
* **The Workflow**: The process begins when a patient submits an unstructured, free-text message through a health portal like MyChart. The system evaluates the text, classifies it into one of four specific departments (Billing, Scheduling, Clinical, or IT_Support), and automatically logs the ticket into the hospital's helpdesk database using an Oracle SQL INSERT statement.
* **The Problem**: Patients frequently send messages to the incorrect department, such as asking a clinician about a billing charge or asking an IT desk about laboratory results.
* **Business Value**: Manually triaging these messages wastes specialized clinical time and causes response delays. Automating this routing reduces latency and saves significant administrative effort.

## 2. Solution and Design

* **What was Built**: A full-stack Streamlit web application simulating a secure patient-to-provider messaging ecosystem. It includes a patient-facing interface for composing messages and a staff-facing command center for routing and archiving tickets.
* **Key GenAI Design Choices**:
    * **Model selection**: The app uses Groq's llama-3.3-70b-versatile model for high-speed semantic analysis.
    * **Structured Outputs**: The system prompt enforces strict JSON formatting, requiring the model to return both the category label and a valid Oracle SQL command.
    * **Context Engineering**: Few-shot prompting is used to train the model on ambiguous edge cases, such as prioritizing clinical symptoms over administrative requests.
* **Why GenAI is Useful**: Patients use highly variable and conversational language. GenAI understands the semantic intent of a full sentence, whereas traditional keyword-based tools fail when vocabulary overlaps across different intents.

## 3. Evaluation and Results

The evaluation methodology utilized an automated metrics framework to rigorously test LLM classification accuracy.

* **Testing Method**: I utilized a "Golden Set" consisting of 50 synthetic, non-PHI patient portal messages. This set was evenly distributed across categories and included over 10 complex edge cases with mixed intents to thoroughly test process evaluation and trajectory handling.
* **The Baseline**: I compared the GenAI system against a "Status Quo" baseline—a Python script using simple keyword matching for strings like "pay," "appointment," and "password".
* **What Counted as Good Output**: I utilized automated metrics for Output Evaluation. An output was marked as a "Pass" only if the LLM's predicted category was an exact string match with the true category defined in the Golden Set.
* **Evaluation Results**: The GenAI model achieved a 96.0% accuracy rate, significantly outperforming the legacy baseline, which scored 44.0%.
* **Findings**:
    * **What Worked**: The LLM successfully caught semantic nuances. For instance, the baseline failed to classify "payment plan" because it only looked for the exact word "pay," whereas the LLM correctly routed it to Billing.
    * **Where it Broke Down**: The legacy system completely failed on overlapping substrings. It misrouted scheduling requests to IT Support simply because the word "appointment" contains the letters "app".
   * **Where the GenAI Struggled (The 4% Error Rate)**: While highly accurate, the Llama-3 model occasionally struggled with perfectly balanced multi-intent messages. When a patient presented two equally weighted administrative requests without a clear primary focus, the model had to "guess" the dominant intent, accounting for the 4% gap in total accuracy.
* **Human-in-the-Loop (HITL) and Edge Cases**: This system is designed as an AI co-pilot, where human staff retains ultimate control over the enterprise database. Every single ticket, regardless of category, is staged in a 'Pending' queue, and a human agent must actively click "Commit" to execute the SQL command. Within this universal workflow, there are two specific edge-case handlers. First, a strict clinical fail-safe is hardcoded into the pipeline: any message mentioning keywords like "pain" or "bleeding" bypasses the LLM's logic and is automatically categorized as 'Clinical' to ensure medical emergencies are never misrouted by the AI. Second, for complex multi-intent messages—such as a patient asking an IT login question and a Scheduling question in the same sentence—the LLM is constrained to route based on the primary dominant intent. Because the human agent reviews every ticket before it is committed, they can process the AI's primary routing and then manually handle the secondary request. The AI handles the bulk semantic sorting, but the human acts as the final clinical and administrative validator.


## 4. Artifact Snapshot

Project Walkthrough Video: https://youtu.be/izek4Y9ahcI



## Instructions for the Grader

### Deployment and Cloud Access

The application is fully hosted on Streamlit Community Cloud for immediate review. You can access the live system via the link at the top of this README. All necessary API keys and secrets are already configured securely in the cloud environment.

### Step-by-Step Evaluation Guide (Live App)

To properly evaluate the workflow as designed, please follow this sequence:

1. **Patient Submission**: Select "Log in as Patient". Compose and send a message in the Secure Messaging Center (for example: "My knee hurts a lot today and I need to reschedule my physical.").
2. **Inbox Verification**: Navigate to the Secure Inbox tab. You will see the message instantly appear, marked as "Pending Triage" and awaiting assignment.
3. **Staff Triage**: Click "Log Out" in the upper right, then select "Log in as Staff". In the Active Queue tab, you will find the message you just sent.
4. **Routing Protocol**: Click "Execute Routing Protocol." Observe how the GenAI correctly identifies the clinical priority over the scheduling request and outputs the generated SQL command, while the legacy baseline may display a context discrepancy warning.
5. **Database Commit**: Click "Commit to Database & Archive Ticket." This simulates the enterprise handoff, clears the queue, and updates the patient's record.
6. **Batch Testing**: Scroll to the bottom of the Staff Dashboard and expand the "System Administration: Execute Batch Evaluation" section. Click "Initialize Test Sequence" to run the full 50-message Golden Set and view the comparative accuracy metrics between the AI and the legacy model.

### Local Installation (Optional Fallback)

If you prefer to run the system locally on your own machine rather than using the cloud deployment, follow these steps:

1. Clone the repository:
   ```bash
   git clone <your-repository-link>
   cd <your-repository-folder>
   ```

2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your API credentials:
   This application relies on the Groq API. To ensure security, the app uses Streamlit's secrets manager. You must provide your own Groq API key:
   * Create a folder named `.streamlit` in the root directory.
   * Inside that folder, create a file named `secrets.toml`.
   * Add your Groq API key in the following format:
     ```toml
     GROQ_API_KEY = "gsk_your_key_here"
     ```

4. Launch the application:
   ```bash
   streamlit run app.py
   ```
