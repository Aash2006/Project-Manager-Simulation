```mermaid
flowchart TD
    classDef page fill:#e3f2fd,stroke:#0d47a1,stroke-width:2px,color:#000;
    classDef action fill:#fff3e0,stroke:#e65100,stroke-width:1px,stroke-dasharray: 5 5,color:#000;

    Disclaimer1[DISCLAIMER:This is an App Navigation Flow for the user during the gameplay, not a formal Sequence Diagram.]
    style Disclaimer1 fill:#fff3cd,stroke:#ffeeba,color:#856404

    UserFlow(User Flow Pages):::page

    UserFlow --> |Continue or new game|CurrentLoadedPage
    Navbar --> |Main Menu|UserFlow
    CurrentLoadedPage --> StartDay
    CurrentLoadedPage --> DecisionDialogue
    CurrentLoadedPage <--> Navbar

    StartDay --> Deadline
    Deadline --> |Yes|ResultsPage
    Deadline --> |No|Minigame --> CurrentLoadedPage 

    subgraph Game flow
        
        Deadline{Has deadline been reached?}
        Minigame["Play Minigame (chance to pop up)"]
        subgraph Always visible
            
            CurrentLoadedPage("Current loaded page (default is game dashboard)"):::page
            Navbar{"Navigation bar for changing current loaded page"}
            DecisionDialogue[Chat box for decisions]:::action
            StartDay[Start day]:::action
        end

        GameDashboardPage(Game dashboard page):::page
        TeamPage(Teams page):::page
        TasksPage(Tasks page):::page
        RelationshipsPage(Relationships page):::page
        StatisticsPage(Statistics Page):::page

        Navbar --- StatisticsPage
        Navbar --- GameDashboardPage
        Navbar --- TeamPage
        Navbar --- TasksPage
        Navbar --- RelationshipsPage
    end

    ResultsPage(Results page):::page

    ResultsPage --> |Once finished looking at the results|UserFlow