
  

## Table of Contents

1. [Application Overview](#application-overview)

2. [Core Chat Features](#core-chat-features)

3. [Multi-Agent Architecture](#multi-agent-architecture)

4. [File Management System](#file-management-system)

5. [Enterprise Features](#enterprise-features)

6. [User Interface Components](#user-interface-components)

7. [Technical Implementation](#technical-implementation)

8. [API Endpoints](#api-endpoints)

9. [Configuration and Deployment](#configuration-and-deployment)

10. [Development and Extension Guide](#development-and-extension-guide)

  

---

  

## Application Overview

  

The EDAV AI Chat Application is a sophisticated enterprise-level chatbot system developed for the CDC (Centers for Disease Control and Prevention). It provides multiple AI interaction modes, enterprise-grade security, and specialized data analysis capabilities.

  

### Key Capabilities

- **Multi-Modal AI Interactions**: Standard GPT conversations, RAG-enabled document search, and specialized SQL agents

- **Enterprise Security**: Azure AD authentication with role-based access control

- **Document Processing**: Upload and analyze various file types with intelligent text extraction

- **Conversation Management**: Persistent chat history with search and export capabilities

- **Administrative Controls**: Comprehensive configuration and user management

  

### Technology Stack

- **Frontend**: React with TypeScript, Fluent UI components

- **Backend**: FastAPI (Python) with async support

- **Database**: Azure CosmosDB for conversation storage

- **Storage**: Azure Blob Storage for file management

- **AI Services**: Azure OpenAI with multiple model support

- **Search**: Azure Cognitive Search for document retrieval

- **Authentication**: Azure Active Directory (Azure AD)

  

---

  

## Core Chat Features

  

### 1. Standard GPT Conversations

  

**User Experience:**

- Real-time streaming responses from OpenAI GPT models

- Support for multiple GPT model profiles (GPT-3.5, GPT-4, GPT-4.1)

- Configurable parameters (temperature, max tokens, frequency penalty)

- Conversation history persistence and retrieval

  

**Technical Implementation:**

- **Endpoint**: `/history/generate`

- **Model Support**: Multiple Azure OpenAI deployments

- **Streaming**: Server-sent events for real-time response delivery

- **Token Management**: Automatic token limit enforcement per model

- **Error Handling**: Comprehensive error messages for rate limits, content filtering

  

**Configuration Options:**

- Temperature (0.0-1.0): Controls response creativity

- Max Tokens: Limits response length

- Top P: Nucleus sampling parameter

- Frequency/Presence Penalty: Reduces repetitive content

- Stop Sequences: Custom termination strings

  

### 2. RAG (Retrieval Augmented Generation)

  

**User Experience:**

- Ask questions about uploaded documents and knowledge bases

- Receive answers with source citations and downloadable references

- Support for multiple document types and knowledge repositories

- Semantic search with Azure Cognitive Search integration

  

**Technical Implementation:**

- **Endpoint**: `/rrr` (Read-Retrieve-Read)

- **Search Engine**: Azure Cognitive Search with semantic ranking

- **Embedding Model**: Configurable embedding deployments

- **Citation System**: Automatic source attribution with download links

- **Vector Search**: Hybrid search combining keyword and semantic matching

  

**RAG Profile System:**

- **Multiple Data Sources**: Each RAG profile connects to different knowledge bases

- **Configurable Search**: Custom search indices, embedding models, and prompt templates

- **Access Control**: Group-based access to specific RAG profiles

- **Prompt Customization**: Override system prompts and few-shot examples

  

**Search Capabilities:**

- **Semantic Ranking**: Advanced semantic understanding for better relevance

- **Folder Filtering**: Restrict search to specific document folders

- **Tag Filtering**: Search within tagged document sets

- **Top-N Results**: Configurable number of search results (5-12)

  

### 3. Agent Conversations

  

**User Experience:**

- Specialized AI agents for specific tasks (currently SQL analysis)

- Tool-equipped agents that can perform actions beyond text generation

- Seamless integration with standard chat interface

- Real-time execution of agent tools and capabilities

  

**Technical Implementation:**

- **Framework**: PydanticAI for robust agent architecture

- **Endpoint**: `/agentconversation/run`

- **Agent Profiles**: Configurable agent definitions with tool assignments

- **Tool System**: Extensible tool framework for specialized capabilities

  

---

  

## Multi-Agent Architecture

  

### Agent Framework Overview

  

The application uses **PydanticAI** to implement a sophisticated multi-agent system that extends beyond simple chat interactions.

  

**Key Components:**

- **Agent Profiles**: Database-stored configurations defining agent capabilities

- **Tool System**: Pluggable tools that agents can use to perform specific tasks

- **Context Management**: Sophisticated conversation context handling across agent interactions

- **Permission System**: Role-based access to different agents

  

### SQL Assistant Agent

  

**User Experience:**

- Natural language queries about database content

- Automatic SQL generation and execution

- Data visualization support with CSV export

- Read-only database access for security

  

**Capabilities:**

- **Schema Introspection**: Automatically understands database structure

- **Query Generation**: Converts natural language to SQL

- **Data Export**: Export results to CSV for further analysis

- **Safety Features**: Strictly read-only operations, no data modification

  

**Technical Implementation:**

- **Database**: Azure Synapse connectivity

- **Authentication**: Service Principal authentication for secure access

- **Tools Available**:

- `get_table_schema()`: Retrieve database schema information

- `run_sql_query()`: Execute SELECT queries safely

- `export_to_csv()`: Export query results for visualization

  

**Security Features:**

- **Read-Only Access**: Only SELECT statements allowed

- **Query Validation**: Automatic SQL syntax and security checking

- **Service Principal Auth**: No user credentials stored or transmitted

- **Error Handling**: Robust error management with retry logic

  

### Agent Profile Management

  

**Administrative Features:**

- **Profile Configuration**: Define agent capabilities, tools, and access permissions

- **Group-Based Access**: Control which users can access specific agents

- **Ordering System**: Define agent presentation order in UI

- **General Availability**: Toggle agents between restricted and public access

  

**Database Structure:**

- **Container**: `agent_profiles` in CosmosDB

- **Partition Key**: `agents`

- **Access Control**: `available_to_group_ids` array for group restrictions

- **Configuration**: Tool assignments, system prompts, model configurations

  

---

  

## File Management System

  

### Upload and Processing Pipeline

  

**User Experience:**

- Drag-and-drop file upload interface

- Support for multiple file types (PDF, Word, Excel, CSV, TXT)

- Real-time processing status and notifications

- File content integration into conversations

  

**Supported File Types:**

- **Text Files**: .txt, .csv (direct text extraction)

- **Documents**: .pdf, .docx, .xlsx (Azure Form Recognizer processing)

- **Images**: Various formats with OCR text extraction

  

**Technical Implementation:**

- **Upload Endpoint**: `/chatfileupload`

- **Processing Endpoint**: `/chatfileprocessor`

- **Storage**: Azure Blob Storage with conversation-based organization

- **Text Extraction**: Azure Form Recognizer for complex documents

- **Database Tracking**: File metadata stored in CosmosDB

  

### File Processing Workflow

  

1. **Upload**: Files uploaded to Azure Blob Storage

2. **Processing**: Text extraction using Azure Form Recognizer or direct parsing

3. **Storage**: Processed text stored as `.txt` files in blob storage

4. **Integration**: File content made available to AI conversations

5. **Tracking**: File metadata stored in `chatbot_uploaded_files` container

  

**Processing Features:**

- **Automatic Text Extraction**: OCR and document parsing

- **Content Integration**: File content automatically included in AI context

- **Conversation Association**: Files linked to specific conversations

- **Persistence**: Files remain available throughout conversation history

  

### File Management API

  

**Key Endpoints:**

- `POST /chatfileupload`: Upload files to conversation

- `POST /chatfileprocessor`: Process uploaded files for text extraction

- `GET /chatfilelist`: Retrieve uploaded files for conversation

- `GET /conversation/documents`: Get document list for conversation

  

**Database Integration:**

- **File Metadata**: Stored in CosmosDB with conversation linkage

- **Content Storage**: Processed text in Azure Blob Storage

- **Access Control**: User-based file access restrictions

  

---

  

## Enterprise Features

  

### Authentication and Authorization

  

**Azure Active Directory Integration:**

- **SSO Support**: Single sign-on with Azure AD

- **Group-Based Access**: Role-based feature access

- **Token Management**: Automatic token renewal and validation

- **API Security**: All endpoints protected with JWT validation

  

**User Management:**

- **User Profiles**: Persistent user preferences and settings

- **Group Memberships**: Dynamic feature access based on AD groups

- **Session Management**: Secure session handling with automatic expiration

  

**Technical Implementation:**

- **MSAL Integration**: Microsoft Authentication Library for React

- **JWT Validation**: Server-side token verification

- **Middleware**: Authentication middleware on all protected routes

- **Exempt Routes**: Public routes for static content and configuration

  

### Configuration Management

  

**GPT Profile System:**

- **Multiple Models**: Support for different OpenAI model deployments

- **Custom Parameters**: Model-specific configuration (temperature, tokens, penalties)

- **Access Control**: Group-based access to specific models

- **Dynamic Configuration**: Runtime model switching without deployment

  

**RAG Profile Management:**

- **Data Source Configuration**: Multiple knowledge base connections

- **Search Configuration**: Custom search indices and embedding models

- **Prompt Engineering**: Custom system prompts and few-shot examples

- **Access Control**: Group-based access to knowledge repositories

  

**System Prompt Management:**

- **Dynamic Prompts**: Runtime prompt modification without code changes

- **Template System**: Parameterized prompt templates

- **Version Control**: Prompt history and rollback capabilities

- **Context Integration**: File upload and conversation context injection

  

### Administrative Interface

  

**Features Available:**

- **User Management**: View and manage user access

- **Configuration**: Modify system settings and model parameters

- **Monitoring**: System health and usage analytics

- **Content Management**: Manage knowledge bases and documents

  

**Technical Implementation:**

- **Admin Routes**: `/assistant-admin` dedicated administrative interface

- **Permission Checking**: Admin-specific authentication requirements

- **Configuration API**: Dedicated endpoints for system configuration

- **Audit Logging**: Administrative action tracking

  

### Feedback and Analytics System

  

**User Feedback:**

- **Rating System**: 1-5 star rating for conversations

- **Detailed Feedback**: Text feedback with user identification

- **Analytics Dashboard**: Feedback aggregation and reporting

- **Issue Tracking**: Integration with feedback management systems

  

**Technical Implementation:**

- **Feedback Storage**: CosmosDB container for feedback data

- **Rating Analytics**: Aggregated rating statistics

- **User Tracking**: Anonymous usage analytics

- **Export Capabilities**: Feedback data export for analysis

  

---

  

## User Interface Components

  

### Chat Interface

  

**Main Chat View:**

- **Message Display**: Threaded conversation with role-based styling

- **Streaming Responses**: Real-time AI response rendering

- **Citation Panel**: Side panel for source document viewing

- **File Upload Area**: Integrated file management interface

  

**User Experience Features:**

- **Markdown Rendering**: Rich text formatting in responses

- **Code Highlighting**: Syntax highlighting for code blocks

- **Copy/Paste**: Easy content sharing and copying

- **Accessibility**: Full keyboard navigation and screen reader support

  

### Side Panel Features

  

**Chat History:**

- **Conversation List**: Paginated conversation history

- **Search and Filter**: Find specific conversations

- **Conversation Management**: Rename, delete, export conversations

- **Quick Access**: Recent conversation shortcuts

  

**Configuration Panel:**

- **Model Selection**: Choose between available GPT profiles

- **Parameter Adjustment**: Real-time parameter modification

- **RAG Profile Selection**: Switch between knowledge bases

- **Agent Selection**: Choose specialized agents for tasks

  

### Component Architecture

  

**React Component Structure:**

- **Layout Components**: `Layout.tsx`, `AdminLayout.tsx`

- **Chat Components**: `Chat.tsx`, `Answer.tsx`, `QuestionInput.tsx`

- **File Management**: `ChatFileManager.tsx`, `UploadedFileNotifications.tsx`

- **Navigation**: `SidePanel.tsx`, `ChatHistory.tsx`

- **Authentication**: `ProtectedRoute.tsx`, `UserProfileMenu.tsx`

  

**State Management:**

- **Global State**: React Context with useReducer for application state

- **Local State**: Component-level state for UI interactions

- **API Integration**: Custom hooks for API calls and data management

  

---

  

## Technical Implementation

  

### Backend Architecture

  

**FastAPI Application Structure:**

- **Main Application**: `main.py` - Core FastAPI app with middleware and routing

- **Routers**: Modular routing for different feature areas

- **Dependencies**: Dependency injection for database and service connections

- **Middleware**: Authentication, CORS, and compression middleware

  

**Key Backend Components:**

- **Authentication Manager**: `AuthManager` for JWT validation and user management

- **Database Services**: Async CosmosDB clients for data persistence

- **AI Services**: OpenAI integration with streaming support

- **File Processing**: Azure Form Recognizer integration

- **Search Services**: Azure Cognitive Search integration

  

### Database Design

  

**CosmosDB Containers:**

- **conversations**: Chat conversation metadata and history

- **messages**: Individual chat messages with conversation linkage

- **rag_profiles**: RAG configuration profiles

- **agent_profiles**: Agent configuration and permissions

- **chatbot_uploaded_files**: File upload metadata

- **user_preferences**: User-specific settings and preferences

- **feedback**: User feedback and ratings

  

**Data Models:**

- **Conversation**: Conversation metadata, user association, configuration

- **Message**: Individual messages with role, content, citations

- **ChatRequest**: Request model for chat interactions

- **AgentProfile**: Agent configuration and tool assignments

  

### API Design Patterns

  

**RESTful Endpoints:**

- **Resource-based URLs**: Clear resource identification

- **HTTP Method Usage**: Appropriate GET, POST, PUT, DELETE usage

- **Status Codes**: Proper HTTP status code returns

- **Error Handling**: Consistent error response format

  

**Async Programming:**

- **Async/Await**: Full async support throughout application

- **Streaming Responses**: Server-sent events for real-time updates

- **Connection Pooling**: Efficient database connection management

- **Concurrent Processing**: Parallel processing where appropriate

  

### Security Implementation

  

**Authentication:**

- **JWT Validation**: Token-based authentication with Azure AD

- **Role-Based Access**: Group membership validation

- **Route Protection**: Middleware-based route protection

- **Token Refresh**: Automatic token renewal handling

  

**Data Security:**

- **Input Validation**: Comprehensive input sanitization

- **SQL Injection Prevention**: Parameterized queries

- **File Upload Security**: File type validation and scanning

- **CORS Configuration**: Proper cross-origin resource sharing

  

---

  

## API Endpoints

  

### Chat and Conversation Endpoints

  

**Core Chat Functionality:**

- `POST /history/generate` - Generate standard GPT responses

- `POST /rrr` - RAG-enabled conversations with document search

- `POST /agentconversation/run` - Agent-based conversations

- `POST /history/update` - Update conversation with new messages

  

**Conversation Management:**

- `GET /history/list/page` - Paginated conversation list

- `POST /history/read` - Read specific conversation

- `POST /history/rename` - Rename conversation

- `DELETE /history/delete` - Delete specific conversation

- `DELETE /history/delete_all` - Delete all user conversations

- `POST /history/clear` - Clear messages from conversation

- `GET /history/download` - Export conversation as text file

  

### File Management Endpoints

  

**File Operations:**

- `POST /chatfileupload` - Upload files to conversation

- `POST /chatfileprocessor` - Process uploaded files

- `GET /chatfilelist` - List files for conversation

- `GET /conversation/documents` - Get conversation documents

- `GET /citation/download/{file_path}` - Download source documents

  

### Configuration and Administration

  

**Configuration:**

- `GET /config` - Get application configuration

- `GET /ragprofiles` - Get available RAG profiles

- `GET /preferences/default` - Get user default preferences

- `POST /preferences/save` - Save user preferences

- `GET /agentconversation/agent_profiles` - Get available agents

  

**System Management:**

- `GET /history/ensure` - Verify CosmosDB connectivity

- `POST /create-log-container` - Initialize logging container

- `POST /create-app-settings-container` - Initialize settings container

- `POST /feedback/submit` - Submit user feedback

- `GET /feedback/ratings` - Get feedback analytics

  

### Placeholder and Utility Endpoints

  

**Conversation Management:**

- `POST /conversations/placeholder` - Create placeholder conversation

- `POST /create-assistantadminsettings-container` - Initialize admin settings

  

**Static Content:**

- `GET /` - Serve main application

- `GET /assistant-admin` - Serve admin interface

- `GET /favicon.ico` - Application favicon

- `GET /assets/{path}` - Static asset serving

  

---

  

## Configuration and Deployment

  

### Environment Configuration

  

**Required Environment Variables:**

```

# Azure OpenAI Configuration

AZURE_OPENAI_SERVICE=your-openai-service

AZURE_OPENAI_SERVICE_KEY=your-api-key

AZURE_OPENAI_CHATGPT_DEPLOYMENT=your-deployment

  

# CosmosDB Configuration

AZURE_COSMOSDB_ACCOUNT=your-cosmos-account

AZURE_COSMOSDB_ACCOUNT_KEY=your-cosmos-key

AZURE_COSMOSDB_DATABASE=your-database-name

  

# Azure Blob Storage

AZURE_BLOB_STORAGE_ACCOUNT=your-storage-account

AZURE_BLOB_STORAGE_KEY=your-storage-key

AZURE_BLOB_STORAGE_USER_UPLOAD_CONTAINER=user-uploads

  

# Azure Form Recognizer

FORM_RECOGNIZER_ENDPOINT=your-form-recognizer-endpoint

FORM_RECOGNIZER_KEY=your-form-recognizer-key

  

# Synapse Database (for SQL Agent)

SYNAPSE_DRIVER=your-odbc-driver

SYNAPSE_SERVER=your-synapse-server

SYNAPSE_DATABASE=your-database

SYNAPSE_SCHEMA=your-schema

SYNAPSE_TABLE=your-table

SYNAPSE_SP_CLIENT_ID=your-service-principal-id

SYNAPSE_SP_CLIENT_SECRET=your-service-principal-secret

SYNAPSE_SP_TENANT_ID=your-tenant-id

```

  

### Deployment Architecture

  

**Frontend Deployment:**

- **Build Process**: TypeScript compilation and Vite bundling

- **Static Hosting**: Served as static files from FastAPI

- **CDN Integration**: Optional CDN for static asset acceleration

  

**Backend Deployment:**

- **FastAPI Application**: Python web application with uvicorn

- **Container Support**: Docker containerization available

- **Azure App Service**: Recommended Azure deployment target

- **Environment Configuration**: Azure App Configuration integration

  

**Database Setup:**

- **CosmosDB Containers**: Automatic container creation on startup

- **Index Configuration**: Optimized indices for query performance

- **Backup Strategy**: Automated backup and disaster recovery

  

### Development Setup

  

**Prerequisites:**

- Python 3.8+ with virtual environment

- Node.js 20+ with npm

- Azure CLI for resource management

- Access to Azure OpenAI and other required services

  

**Installation Process:**

1. **Clone Repository**: `git clone [repository-url]`

2. **Python Environment**: Create and activate virtual environment

3. **Install Dependencies**: `pip install -r requirements.txt`

4. **Frontend Setup**: `cd frontend && npm install`

5. **Environment Configuration**: Copy `.env.sample` to `.env` and configure

6. **Database Initialization**: Run container creation endpoints

7. **Start Services**: Use provided batch scripts or manual startup

  

**Utility Scripts:**

- `scripts/install.bat` - Automated dependency installation

- `scripts/start.bat` - Start both frontend and backend

- `scripts/start_backend.bat` - Start backend only

- `scripts/start_frontend.bat` - Start frontend only

  

---

  

## Development and Extension Guide

  

### Adding New Features

  

**Creating New Agents:**

1. **Define Agent Profile**: Create agent configuration in CosmosDB

2. **Implement Tools**: Create tool functions in `backend/agents/[agent-name]/tools.py`

3. **Configure Prompts**: Define system prompts in `backend/agents/[agent-name]/prompts.py`

4. **Register Agent**: Add agent to routing and service layers

5. **Test Integration**: Verify agent functionality and tool execution

  

**Adding New RAG Profiles:**

1. **Configure Data Source**: Set up Azure Cognitive Search index

2. **Create Profile**: Add RAG profile configuration to CosmosDB

3. **Test Search**: Verify document retrieval and citation generation

4. **Set Permissions**: Configure group-based access if needed

  

**Extending File Processing:**

1. **Add File Type Support**: Extend file type validation

2. **Implement Processing**: Add processing logic for new file types

3. **Update UI**: Modify upload interface to support new types

4. **Test Pipeline**: Verify end-to-end file processing workflow

  

### Common Extension Patterns

  

**Adding New Endpoints:**

```python

@router.post("/new-feature")

async def new_feature(

request: Request,

data: CustomRequest = Body(...),

user: dict = Depends(get_authenticated_user)

):

# Implementation here

pass

```

  

**Creating New Components:**

```typescript

interface NewComponentProps {

// Define props

}

  

const NewComponent: React.FC<NewComponentProps> = ({ props }) => {

// Implementation here

return <div>Component content</div>;

};

```

  

**Database Operations:**

```python

# Adding new CosmosDB operations

async def create_new_entity(self, entity_data: dict):

return await self.container_client.create_item(entity_data)

```

  

### Testing Strategies

  

**Backend Testing:**

- **Unit Tests**: Test individual functions and classes

- **Integration Tests**: Test API endpoints and database operations

- **Load Testing**: Verify performance under concurrent load

- **Security Testing**: Validate authentication and authorization

  

**Frontend Testing:**

- **Component Tests**: Test React component behavior

- **Integration Tests**: Test user interaction flows

- **Cross-Browser Testing**: Verify compatibility across browsers

- **Accessibility Testing**: Ensure compliance with accessibility standards

  

### Debugging and Monitoring

  

**Logging Configuration:**

- **Structured Logging**: JSON-formatted logs for analysis

- **CosmosDB Logging**: Optional logging to CosmosDB for analytics

- **Error Tracking**: Comprehensive error logging with context

- **Performance Monitoring**: Request timing and resource usage

  

**Development Tools:**

- **Hot Reload**: Frontend development with hot module replacement

- **API Testing**: Tools like Postman for endpoint testing

- **Database Exploration**: CosmosDB Data Explorer for data inspection

- **Log Analysis**: Azure Application Insights integration

  

### Best Practices

  

**Code Organization:**

- **Modular Structure**: Separate concerns into distinct modules

- **Type Safety**: Full TypeScript usage for frontend, type hints for backend

- **Error Handling**: Comprehensive error handling at all layers

- **Documentation**: Inline documentation and API documentation

  

**Security Considerations:**

- **Input Validation**: Validate all user inputs

- **Authentication**: Verify user authentication on all protected routes

- **Authorization**: Check user permissions for resource access

- **Data Sanitization**: Sanitize data before storage and display

  

**Performance Optimization:**

- **Database Indexing**: Optimize CosmosDB queries with proper indexing

- **Caching**: Implement caching for frequently accessed data

- **Async Operations**: Use async/await for I/O operations

- **Resource Management**: Proper cleanup of connections and resources

  

---

  

## Conclusion

  

The EDAV AI Chat Application represents a comprehensive enterprise AI platform with sophisticated conversation capabilities, multi-agent architecture, and robust file processing features. This documentation provides both user guidance and technical implementation details to support ongoing development and feature extensions.

  

For additional support or questions about specific features, refer to the source code in the respective modules or contact the development team.

  

**Key Strengths:**

- **Modular Architecture**: Easy to extend and modify

- **Enterprise Security**: Comprehensive authentication and authorization

- **Multi-Modal AI**: Standard chat, RAG search, and specialized agents

- **Rich File Processing**: Support for multiple document types

- **Robust Error Handling**: Comprehensive error management

- **Scalable Design**: Built for enterprise-scale deployment

  

**Future Extension Opportunities:**

- **Additional Agents**: Expand agent capabilities for specialized tasks

- **Enhanced Analytics**: More detailed usage and performance analytics

- **Advanced File Processing**: Support for additional file types and processing methods

- **Integration Capabilities**: APIs for external system integration

- **Mobile Support**: Enhanced mobile interface and functionality