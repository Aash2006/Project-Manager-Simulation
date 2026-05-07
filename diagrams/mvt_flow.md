```mermaid
%%{init: { 'themeVariables': { 'fontSize': '13px' } } }%%
flowchart TB
    subgraph Regular Django MVT
        direction TB
        User2(User) --> Browser2(Browser)

        subgraph Transport2 [Request/Response Methods]
            HTTP2[HTTP: Full Reload]
        end

        subgraph Django2 [Django Server]
            View2(View)
            Model2(Model)
            Template2(Template)
            
            View2 <--> |CRUD| Model2
            View2 <--> |Context & HTML String| Template2
        end

        Browser2 --> |"Non-JS trigger"| HTTP2
        
        HTTP2 <--> |Request & Response| View2
        HTTP2 -.-> |Full Refresh| Browser2
    end
    subgraph Enhanced Django MVT with AJAX
        direction TB
        Note[We are using this strcuture.]
        User(User) --> Browser(Browser)

        subgraph Transport [Request/Response Methods]
            
            HTTP[HTTP: Full Reload]
            JS[JS: Background Update]
        end

        subgraph Django [Django Server]
            Note2["Service acts as abstraction to keep code modular. Some views use it, some don't because of their simplicity."]
            View(View)
            Model(Model)
            Template(Template)
            
            View --> |Parameters/Request Data|Service
            View <--> |Direct Query|Regular[Without service]
            Service <--> |CRUD| Model
            Service <--> |Context & HTML String| Template
            Service --> |Context reflecting changes|View
            Regular <--> |CRUD| Model
            Regular <--> |Context & HTML String| Template
            Regular --> |Context reflecting changes|View
        end

        %% Connection Logic
        Browser --> |Non-JS trigger| HTTP
        Browser --> |JS triggers fetch| JS
        
        HTTP <--> |Request & Response| View
        JS <--> |Request & Response| View

        %% Return to Browser
        HTTP -.-> |Full Refresh| Browser
        JS -.-> |"DOM Update (No full refresh)"| Browser
    end