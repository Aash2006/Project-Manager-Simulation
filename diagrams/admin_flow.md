```mermaid
flowchart TD
    classDef page fill:#e3f2fd,stroke:#0d47a1,stroke-width:2px,color:#000;
    classDef action fill:#fff3e0,stroke:#e65100,stroke-width:1px,stroke-dasharray: 5 5,color:#000;

    Disclaimer1[DISCLAIMER:This is an App Navigation Flow for the admin, not a formal Sequence Diagram.]
    style Disclaimer1 fill:#fff3cd,stroke:#ffeeba,color:#856404

    subgraph Login_Flow [Login Flow]
        LoginPage(Login Page):::page
        LoginAction[Login Form]:::action
        ValidateLogin{Validate Login}
        
        LoginPage --> LoginAction
        LoginAction --> ValidateLogin
        ValidateLogin --> |Invalid login| LoginPage
    end

    ValidateLogin --> |Success|CurrentLoadedPage

    subgraph Admin_Flow [Admin flow]
        subgraph Always [Always loaded]
            CurrentLoadedPage("Current loaded page (Default is Admin dashboard) "):::page
            Navbar{Navigation bar}

            CurrentLoadedPage <--> Navbar
            CurrentLoadedPage --> |Logout|LoginPage
        end

        Navbar --- AdminDashboard
        Navbar --- AdminStatistics
        Navbar --- AdminSettings
        Navbar --- DjangoAdmin
        AdminDashboard(Admin Dashboard):::page
        AdminStatistics(Admin Statistics):::page
        AdminSettings(Admin Statistics):::page
        DjangoAdmin(Django Admin panel):::page

    end
