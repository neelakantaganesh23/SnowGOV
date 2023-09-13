import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import matplotlib.pyplot as plt
import numpy as np
#connect to snowflake function
SNOWFLAKE_CONFIG = {
    "account": "xh84085.ap-southeast-1",
    "user": "sravani12",
    "password": "Sravani@12",
    "role": "accountadmin",
    "warehouse": "COMPUTE_WH",
    "database": "UTIL_DB",
    "schema": "ADMIN_TOOLS"
}
if "grant_users" not in st.session_state:
    st.session_state.grant_users = []
def apply_css_styles():
    # Set the background color of the main page
    st.markdown("<style>body {background-color: #3498DB;}</style>", unsafe_allow_html=True)
    # Set the background color of the Streamlit navigation bar
    st.markdown("<style>.sidebar .sidebar-content {background-color: #2980B9; color: white;}</style>", unsafe_allow_html=True)
def connect_to_snowflake(conn_params):
    return snowflake.connector.connect(**conn_params)  # <-- Corrected line
def snowflake_connection():
    st.markdown("<style>.reportview-container .main .block-container {background-color: #DCEEFB;}</style>", unsafe_allow_html=True)
    st.title("LOGIN:")
    account_name = st.text_input("Name this Connection:")
    account_url = st.text_input("Account URL:")
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")
    account_parts = account_url.split('.') if account_url else []
    snowflake_account = account_parts[0] if len(account_parts) > 0 else ""
    region = account_parts[1] if len(account_parts) > 1 else ""
    conn_params = {
        "user": username,
        "password": password,
        "account": snowflake_account,
        "region": region,
    }
    if st.button("Connect"):
        try:
            conn = connect_to_snowflake(conn_params)
            if conn:
                st.session_state.conn = conn
                st.session_state.connections[account_name] = conn_params
                st.success(f"🔗 Connected to {account_name}!")
            else:
                st.error("Unable to establish a connection.")
        except snowflake.connector.errors.DatabaseError as e:  # <-- Corrected exception
            st.error(f"🚫 Connection failed. Error: {e}")
            st.markdown("</div>", unsafe_allow_html=True)
def create_database_and_schema(conn, environment, team_name, sub_team_name):
    cursor = conn.cursor()
    result_messages = []
    try:
        procedure_name_db = "UTIL_DB.ADMIN_TOOLS.SETUP_DATA_MART"
        call_query_db = f"CALL {procedure_name_db}(%s, %s, %s)"
        cursor.execute(call_query_db, (environment, team_name, sub_team_name))
        result_messages=cursor.fetchall()
        return result_messages[0][0]
    except Exception as e:
        result_messages.append(f"Error creating database: {e}")
    cursor.close()
    return "\n".join(result_messages)
def set_role(conn, role_name="ACCOUNTADMIN"):
    """Set the role for the current Snowflake session."""
    cursor = conn.cursor()
    try:
        cursor.execute(f"USE ROLE {role_name};")
    except Exception as e:
        st.error(f"Error setting role: {e}")
    finally:
        cursor.close()
def create_schema(conn, environment, team_name, sub_team_name, schema_name, power_user_privilege, analyst_privilege, data_engineer_privilege):
    cursor = conn.cursor()
    try:
        procedure_name = "UTIL_DB.ADMIN_TOOLS.SETUP_SCHEMA_V3"
        call_query = f"CALL {procedure_name}(%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(call_query, (environment, team_name, sub_team_name, schema_name, power_user_privilege, analyst_privilege, data_engineer_privilege))
        return f"Schema for {sub_team_name} in {environment} environment created successfully."
    except Exception as e:
        return f"Error creating schema: {e}"
    finally:
        cursor.close()
def database_management():
    choose = option_menu(
        menu_title="DATABASE MANAGEMENT",
        options=["Database", "Schema"],
        icons=["database-fill-add", "database-fill-lock"],
        orientation="horizontal",
        menu_icon="database-fill-gear"
    )
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    # Database Section
    environment = ''
    db_team_name = ''
    db_sub_team_name = ''
    if choose == 'Database':
        #st.write("Create DataBase")
        environment = st.selectbox('ENVIRONMENT :', ['DEV', 'PROD', 'STAGE', 'TEST'])
        db_team_name = st.text_input('PROJECT :', key="db_team_name_input")
        db_sub_team_name = st.text_input('SUBJECT_AREA :', key="db_sub_team_name_input")
        # Store the values in session_state
        st.session_state.environment = environment
        st.session_state.db_team_name = db_team_name
        st.session_state.db_sub_team_name = db_sub_team_name
        if st.button('SETUP'):
            set_role(conn, "ACCOUNTADMIN")
            message = create_database_and_schema(conn, environment, db_team_name, db_sub_team_name)
            st.write(message)
    if choose == 'Schema':
        #st.write("Create Schema")
        # Retrieve the values from session_state to pre-populate the input fields
        schema_name = st.text_input("SCHEMA :", key="schema_name_input")
        schema_env = st.text_input("PROJECT :", st.session_state.get('environment', ''), key="schema_env_input")
        schema_team_name = st.text_input('PROJECT TEAM :', st.session_state.get('db_team_name', ''), key="schema_team_name_input")
        schema_sub_team_name = st.text_input('PROJECT SUB TEAM :', st.session_state.get('db_sub_team_name', ''), key="schema_sub_team_name_input")
        # Using st.expander for Privilege Assignment
        with st.expander("PRIVILEGE ASSIGNMENT"):
            privilege_options = ["Read Only", "Read/Write", "Full Access"]
            power_user_privilege = st.selectbox("POWER USER", privilege_options, index=2)
            analyst_privilege = st.selectbox("ANALYST", privilege_options, index=1)
            data_engineer_privilege = st.selectbox("DATA ENGINEER", privilege_options, index=0)
            if power_user_privilege == "Read Only" and analyst_privilege == "Full Access":
                st.write("Invalid combination: POWER USER cannot have lower privileges than ANALYST.")
        if st.button('Create'):
            set_role(conn, "ACCOUNTADMIN")
            message = create_schema(conn, schema_env, schema_team_name, schema_sub_team_name, schema_name,
                                    power_user_privilege, analyst_privilege, data_engineer_privilege)
            st.write(message)
def create_snowflake_user(user_name, f_name, l_name, email):
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cursor = conn.cursor()
    try:
        procedure_name = "UTIL_DB.STREAMLIT_TOOLS.CREATE_USER"
        result = cursor.callproc(procedure_name, (user_name, f_name, l_name, email))
        # Check if the result contains the username, indicating successful creation
        if result[0] == user_name:
            return f"User created: {result[0]}"  # Return the desired message with the username
        else:
            return result[0]  # Return the result as it is
    except Exception as e:
        if "already exists" in str(e).lower():  # Check if the error message contains "already exists"
            return "User already exists!"
        else:
            return str(e)
    finally:
        cursor.close()
def user_creation_page():
    not_required = option_menu(
        menu_title = "USER CREATION",
        options = ["User"],
        icons=['person-bounding-box'],
        menu_icon ='person-fill-add'
    )
    user_name = st.text_input("USERNAME :")
    f_name = st.text_input("FIRST NAME :")
    l_name = st.text_input("LAST NAME :")
    email = st.text_input("EMAIL :")
    if st.button("Create"):
        result = create_snowflake_user(user_name, f_name, l_name, email)
        st.write(result)  # This will display "User already exists!" if the user already exists
def role_manage():
    role_choice = option_menu(
        menu_title = "Role Management",
        options = ["Role Assign","List Users","Revoke Role"],
        icons = ["person-check","person-video2","person-fill-slash"],
        orientation = 'horizontal',
        menu_icon = 'person-fill-gear'
    )
    if role_choice == 'Role Assign':
        role_assignment()
    if role_choice == 'List Users':
        role_list()
    if role_choice == 'Revoke Role':
        revoke_role()
def revoke_role():
    con = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    # Calling stored procedure (ensure it populates UTIL_DB.STREAMLIT_TOOLS.ALL_USERS)
    con.cursor().execute("CALL UTIL_DB.STREAMLIT_TOOLS.FETCH_ALL_USERS();")
    # Assuming the first column is the username, fetch them
    users = [row[0] for row in con.cursor().execute("SELECT * FROM UTIL_DB.STREAMLIT_TOOLS.ALL_USERS;").fetchall()]
    # From here on, use your original code:
    selected_user = st.selectbox('Select User', users)
    roles_query = f"SELECT ROLE FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS WHERE GRANTEE_NAME = '{selected_user}'"
    result = con.cursor().execute(roles_query).fetchall()
    roles = [row[0] for row in result]
    st.write(f"Roles already assigned to {selected_user}:")
    st.table(pd.DataFrame(roles, columns=['Roles']))
    roles_to_revoke = st.multiselect('Select Roles to Revoke', roles)
    if st.button('Revoke Role'):
        # Construct the query to call the stored procedure
        roles_array_str = ', '.join([f"'{role}'" for role in roles_to_revoke])
        query = f"CALL UTIL_DB.STREAMLIT_TOOLS.REVOKE_USER_GRANTS('{selected_user}', ARRAY_CONSTRUCT({roles_array_str}))"
        con.cursor().execute(query)
        st.write(f"Roles {', '.join(roles_to_revoke)} revoked from {selected_user}")
    con.close()
def connect_to_snowflake2():
    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None, None
def fetch_all_roles2():
    conn, cursor = connect_to_snowflake2()
    if conn is None or cursor is None:
        return []
    try:
        query = "SELECT DISTINCT Role_Name FROM UTIL_DB.STREAMLIT_TOOLS.SPECIFIC_ROLES"
        cursor.execute(query)
        result = cursor.fetchall()
        return [row[0] for row in result]
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        cursor.close()
        conn.close()
def fetch_users_for_role2(role_name):
    conn, cursor = connect_to_snowflake2()
    if conn is None or cursor is None:
        return None
    try:
        # Adjusted the column name here to UserName
        query = f"SELECT UserName FROM UTIL_DB.STREAMLIT_TOOLS.USERS_ROLES WHERE RoleName = '{role_name}'"
        cursor.execute(query)
        result = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(result, columns=columns)
        return df
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()
def role_list():
    #st.title("Fetch Users for Role")
    roles = fetch_all_roles2()
    if not roles:
        st.warning("No roles found. Check your Snowflake configuration and data.")
    else:
        role_name = st.selectbox("SELECT ROLE :", options=roles)
        get_users_button = st.button("GET")
    # Display users if the button is clicked
        if get_users_button:
            if role_name:
                users_df = fetch_users_for_role2(role_name)
                if users_df is not None and not users_df.empty:
                    st.write(f'USERS FOR ROLE {role_name}:')
                    st.dataframe(users_df)
                else:
                    st.warning(f'No users found for the role {role_name}.')
def execute_query(conn,query):
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchall()
    cur.close()
    return result
def fetch_all_roles(conn):
    cur = conn.cursor()
    # Create a temporary table
    cur.execute("CREATE TEMPORARY TABLE TEMP_ROLES AS SELECT DISTINCT NAME FROM SNOWFLAKE.ACCOUNT_USAGE.ROLES;")
    # Fetch roles from the temporary table
    cur.execute("SELECT NAME FROM TEMP_ROLES;")
    roles = [row[0] for row in cur.fetchall()]
    # Drop the temporary table (optional, as it's temporary and will be dropped automatically at the end of the session)
    cur.execute("DROP TABLE TEMP_ROLES;")
    cur.close()
    return roles
def check_user_grants(conn,username, roles):
    try:
        roles_str = ",".join([f"'{role}'" for role in roles])
        query = f"CALL UTIL_DB.STREAMLIT_TOOLS.USER_GRANTS('{username}', ARRAY_CONSTRUCT({roles_str}))"
        result = execute_query(conn,query)
        return result[0][0] if result else "Error assigning roles."
    except Exception as e:
        return f"Error: {e}"
def fetch_granted_roles(conn,username):
    query = f"""
        SELECT ROLE
        FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS
        WHERE GRANTEE_NAME = '{username}';
    """
    result = execute_query(conn,query)
    return [role[0] for role in result]
def role_assignment():
    # Connect to Snowflake
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    conn.cursor().execute("CALL UTIL_DB.STREAMLIT_TOOLS.FETCH_ALL_USERS();")
    users = execute_query(conn, "SELECT * FROM UTIL_DB.STREAMLIT_TOOLS.ALL_USERS;")
    # Fetch roles only once and store in session state
    if "all_roles" not in st.session_state:
        st.session_state.all_roles = fetch_all_roles(conn)
    # Initialize or get the selected user from session state
    selected_user = st.session_state.get('selected_user', users[0][0])
    user_selection = st.selectbox('SELECT USER :', [user[0] for user in users], index=[user[0] for user in users].index(selected_user))
    with st.expander("Already granted roles"):
        already_granted_roles = fetch_granted_roles(conn, user_selection)
        if already_granted_roles:
            unique_roles = list(set(already_granted_roles))
            st.table({"Roles": already_granted_roles})
        else:
            st.write(f"No roles granted to {user_selection} yet.")
    # Initialize or get the selected roles from session state
    selected_roles = st.session_state.get('selected_roles', [])
    role_selections = st.multiselect('SELECT ROLE :', st.session_state.all_roles, default=selected_roles)
    if st.button("Assign"):
        message = check_user_grants(conn, user_selection, role_selections)
        st.write(message)
        # Update the session state with the current selections
        st.session_state.selected_user = user_selection
        st.session_state.selected_roles = role_selections
    conn.close()
def monitor():
    st.write("PROGRESS")
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cur = conn.cursor()
    df1= cur.execute("select to_decimal(sum(credits_used),15,2) from snowflake.account_usage.warehouse_metering_history;")
    df1 = pd.DataFrame(df1)
    st.write(df1[0][0])
def monitor():
    st.write("PROGRESS")
    dont_choose = option_menu(
        menu_title = "CREDITS USAGE",
        options = ["Monitor"]
    )
    environment = st.selectbox('ENVIRONMENT :', ['DEV', 'PROD', 'STAGE', 'TEST'])
    query = f"""
        select distinct tag_value from SNOWFLAKE.ACCOUNT_USAGE.tag_references where tag_name = 'COST_CENTER'
and domain = 'WAREHOUSE' and LEFT(object_name,3) ='{environment}';
    """
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    #conn.cursor().execute(query)
    projects = execute_query(conn,query)
    project_selection = st.selectbox('PROJECT :', [projects[0] for projects in projects])
    query2 = f"""
select sub_team_name from BILLING_USAGE.DASHBOARD.SUB_TEAM sb
join BILLING_USAGE.DASHBOARD.TEAM_SUB_TEAM_MAPPING m on sb.sub_team_id=m.sub_team_id
join BILLING_USAGE.DASHBOARD.TEAM t on t.team_id = m.team_id where t.team_name = '{project_selection}';
"""
    subj = execute_query(conn,query2)
    subj_selection = st.selectbox('SUBJECT AREA :',[subj[0] for subj in subj])
def Menu_navigator():
    with st.sidebar:
        choice = option_menu(
           menu_title="SNOWGOV",
            options=["USER","DATABASE" ,"ROLE", "MONITOR"],
            icons=[ "people-fill","database-fill", "person-lines-fill", "tv-fill"],
            menu_icon="snow2"
        )
    pages = {
        "User Creation": user_creation_page,
        "Database Management": database_management,
        "Role Management" : role_manage,
        "Monitor" : monitor
    }
    current_page = st.session_state.get("current_page", "User Creation")
    if choice == 'DATABASE':
        current_page = "Database Management"
    elif choice == 'USER':
        current_page = "User Creation"
    elif choice == 'ROLE':
        current_page = "Role Management"
    elif choice == 'MONITOR':
        current_page = "Monitor"
    # Add more elif conditions if you have more choices/pages
    st.session_state.current_page = current_page
    pages[current_page]()
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
# Main function with CSS applied at the beginning
def main():
    st.markdown("<style>body {background-color: #3498DB;}</style>", unsafe_allow_html=True)
    st.markdown("<style>.stButton>button {background-color: #2980B9; color: white;}</style>", unsafe_allow_html=True)
    if "conn" not in st.session_state:
        st.session_state.conn = None
    if "connections" not in st.session_state:
        st.session_state.connections = {}
    Menu_navigator()
if __name__ == "__main__":
    main()
