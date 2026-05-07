```mermaid
%%{init: { 'themeVariables': { 'fontSize': '20px' } } }%%
flowchart TD
    %% Define Styles
    classDef page fill:#e3f2fd,stroke:#0d47a1,stroke-width:2px,color:#000
    classDef action fill:#fff3e0,stroke:#e65100,stroke-width:1px,stroke-dasharray: 5 5,color:#000

    %% Nodes
    Note[DISCLAIMER:This is an App Navigation Flow for the user before the gameplay,<br/>not a formal Sequence Diagram.]
    style Note fill:#fff3cd,stroke:#ffeeba,color:#856404
    
    subgraph Login_Flow [Login Flow]
        LoginPage(Login Page):::page
        ValidateLogin{Validate Login}
        
        LoginPage --> LoginAction[Login Form]:::action
        LoginAction --> ValidateLogin
        ValidateLogin --> |Invalid login| LoginPage
    end

    LoginPage <--> |Go to register/Back to login| RegisterPage

    ValidateLogin --> |Valid Login| DashboardPage

    subgraph Register_Flow [Register Flow]
        RegisterPage(Register Page):::page
        ValidateRegister{Validate Register}

        RegisterPage --> RegisterAction[Register Form]:::action
        RegisterAction --> ValidateRegister
        ValidateRegister --> |Invalid register| RegisterPage
    end

    ValidateRegister --> |Valid Register| DashboardPage

    subgraph Dashboard_Flow [Dashboard Flow]
        DashboardPage(Dashboard Page):::page
    end

    DashboardPage <--> |Play| GameStartPage
    DashboardPage <--> |Settings/Back to dashboard| SettingsPage
    DashboardPage <--> |Statistics/Back to dashboard| StatisticsPage
    DashboardPage --> |Logout| LoginPage

    subgraph Settings_Flow [Settings Flow]
        SettingsPage(Settings Page):::page
    end

    subgraph Statistics_Flow [Statistics Flow]
        StatisticsPage(Statistics Page):::page
    end

    subgraph Game_Start_Flow [Game Start Flow]
        GameStartPage(Game start page):::page
        NewGame[Create a new game]:::action
        ContinueGame[Continue a game]:::action
        CreateTeam[Choose your team for the game]:::action

        GameStartPage --> NewGame
        NewGame --> CreateTeam
        GameStartPage --> |Only if save exists!| ContinueGame
    end

    CreateTeam --> |New save| GameDashboardPage
    ContinueGame --> |Continue save| GameDashboardPage
    
    subgraph Game_Dashboard_Flow [Game Flow]
        GameDashboardPage(Current loaded game page):::page
        Note2[Game flow is continued in another diagram.]
        style Note2 fill:#fff3cd,stroke:#ffeeba,color:#856404
    end

    GameDashboardPage --> |Main Menu| DashboardPage