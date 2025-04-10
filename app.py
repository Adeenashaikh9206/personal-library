import streamlit as st
import pandas as pd
import datetime
from pathlib import Path
import plotly.express as px
import os

# App configuration
st.set_page_config(
    page_title="My Personal Library",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
DATA_FILE = "library_data.csv"
COVER_IMAGE_FOLDER = "book_covers"

# Create necessary folders
Path(COVER_IMAGE_FOLDER).mkdir(exist_ok=True)

# Initialize session state
if 'library_df' not in st.session_state:
    if os.path.exists(DATA_FILE):
        st.session_state.library_df = pd.read_csv(DATA_FILE)
    else:
        st.session_state.library_df = pd.DataFrame(columns=[
            'Title', 'Author', 'ISBN', 'Genre', 'Publication Year', 
            'Pages', 'Current Page', 'Status', 'Rating', 
            'Review', 'Date Added', 'Date Finished', 'Cover Image'
        ])

# Helper functions
def save_data():
    st.session_state.library_df.to_csv(DATA_FILE, index=False)

def handle_cover_upload(uploaded_file, isbn):
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1]
        cover_filename = f"{COVER_IMAGE_FOLDER}/{isbn}.{file_extension}"
        with open(cover_filename, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return cover_filename
    return None

def display_cover(cover_path):
    if cover_path and os.path.exists(cover_path):
        st.image(cover_path, width=150)
    else:
        st.image("https://via.placeholder.com/150x200?text=No+Cover", width=150)

def add_book(title, author, isbn, genre, year, pages, cover_file):
    new_book = {
        'Title': title,
        'Author': author,
        'ISBN': isbn,
        'Genre': genre,
        'Publication Year': year,
        'Pages': pages,
        'Current Page': 0,
        'Status': 'Unread',
        'Rating': 0,
        'Review': '',
        'Date Added': datetime.date.today().strftime("%Y-%m-%d"),
        'Date Finished': '',
        'Cover Image': handle_cover_upload(cover_file, isbn) if cover_file else ''
    }
    
    st.session_state.library_df = pd.concat(
        [st.session_state.library_df, pd.DataFrame([new_book])], 
        ignore_index=True
    )
    save_data()
    st.success("Book added successfully!")

def update_book(index, title, author, isbn, genre, year, pages, current_page, status, rating, review, cover_file):
    st.session_state.library_df.at[index, 'Title'] = title
    st.session_state.library_df.at[index, 'Author'] = author
    st.session_state.library_df.at[index, 'ISBN'] = isbn
    st.session_state.library_df.at[index, 'Genre'] = genre
    st.session_state.library_df.at[index, 'Publication Year'] = year
    st.session_state.library_df.at[index, 'Pages'] = pages
    st.session_state.library_df.at[index, 'Current Page'] = current_page
    st.session_state.library_df.at[index, 'Status'] = status
    st.session_state.library_df.at[index, 'Rating'] = rating
    st.session_state.library_df.at[index, 'Review'] = review
    
    if status == 'Completed' and not st.session_state.library_df.at[index, 'Date Finished']:
        st.session_state.library_df.at[index, 'Date Finished'] = datetime.date.today().strftime("%Y-%m-%d")
    
    if cover_file is not None:
        cover_path = handle_cover_upload(cover_file, isbn)
        if cover_path:
            st.session_state.library_df.at[index, 'Cover Image'] = cover_path
    
    save_data()
    st.success("Book updated successfully!")

def delete_book(index):
    cover_path = st.session_state.library_df.at[index, 'Cover Image']
    if cover_path and os.path.exists(cover_path):
        os.remove(cover_path)
    
    st.session_state.library_df = st.session_state.library_df.drop(index).reset_index(drop=True)
    save_data()
    st.success("Book deleted successfully!")

# UI Components
def show_add_book_form():
    with st.expander("Add New Book", expanded=False):
        with st.form("add_book_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Title*", max_chars=100)
                author = st.text_input("Author*", max_chars=50)
                isbn = st.text_input("ISBN", max_chars=20)
                genre = st.selectbox(
                    "Genre",
                    ["Fiction", "Non-Fiction", "Science Fiction", "Fantasy", 
                     "Mystery", "Thriller", "Romance", "Biography", 
                     "History", "Science", "Self-Help", "Other"]
                )
            
            with col2:
                year = st.number_input("Publication Year", min_value=0, max_value=datetime.date.today().year)
                pages = st.number_input("Total Pages*", min_value=1)
                cover_file = st.file_uploader("Cover Image", type=["jpg", "jpeg", "png"])
            
            submitted = st.form_submit_button("Add Book")
            
            if submitted:
                if not title or not author or not pages:
                    st.error("Please fill in all required fields (marked with *)")
                else:
                    add_book(title, author, isbn, genre, year, pages, cover_file)

def show_book_card(book, index):
    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            display_cover(book['Cover Image'])
        
        with col2:
            st.subheader(book['Title'])
            st.caption(f"by {book['Author']} ({book['Publication Year']})")
            st.write(f"**Genre:** {book['Genre']}")
            st.write(f"**Status:** {book['Status']}")
            
            if book['Status'] in ['Reading', 'Completed']:
                progress = (book['Current Page'] / book['Pages']) * 100
                st.progress(int(progress), f"Page {book['Current Page']} of {book['Pages']} ({progress:.1f}%)")
            
            if book['Rating'] > 0:
                st.write(f"⭐ {'★' * int(book['Rating'])}{'☆' * (5 - int(book['Rating']))} {book['Rating']}/5")
            
            with st.expander("More Details"):
                if book['Review']:
                    st.write("**Review:**")
                    st.write(book['Review'])
                
                edit_col, delete_col, _ = st.columns([1, 1, 3])
                
                with edit_col:
                    if st.button("Edit", key=f"edit_{index}"):
                        st.session_state.edit_index = index
                
                with delete_col:
                    if st.button("Delete", key=f"delete_{index}"):
                        delete_book(index)

def show_edit_book_form():
    if 'edit_index' in st.session_state:
        index = st.session_state.edit_index
        book = st.session_state.library_df.iloc[index]
        
        with st.expander(f"Edit Book: {book['Title']}", expanded=True):
            with st.form("edit_book_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    title = st.text_input("Title*", value=book['Title'], max_chars=100)
                    author = st.text_input("Author*", value=book['Author'], max_chars=50)
                    isbn = st.text_input("ISBN", value=book['ISBN'], max_chars=20)
                    genre = st.selectbox(
                        "Genre",
                        ["Fiction", "Non-Fiction", "Science Fiction", "Fantasy", 
                         "Mystery", "Thriller", "Romance", "Biography", 
                         "History", "Science", "Self-Help", "Other"],
                        index=["Fiction", "Non-Fiction", "Science Fiction", "Fantasy", 
                              "Mystery", "Thriller", "Romance", "Biography", 
                              "History", "Science", "Self-Help", "Other"].index(book['Genre'])
                    )
                
                with col2:
                    year = st.number_input("Publication Year", value=book['Publication Year'], min_value=0, max_value=datetime.date.today().year)
                    pages = st.number_input("Total Pages*", value=book['Pages'], min_value=1)
                    current_page = st.number_input("Current Page", value=book['Current Page'], min_value=0, max_value=book['Pages'])
                    status = st.selectbox(
                        "Status",
                        ["Unread", "Reading", "Completed", "On Hold", "Dropped"],
                        index=["Unread", "Reading", "Completed", "On Hold", "Dropped"].index(book['Status'])
                    )
                    rating = st.slider("Rating", 0, 5, int(book['Rating']))
                    review = st.text_area("Review", value=book['Review'], height=100)
                    cover_file = st.file_uploader("Update Cover Image", type=["jpg", "jpeg", "png"])
                
                col1, col2, _ = st.columns([1, 1, 3])
                
                with col1:
                    submitted = st.form_submit_button("Update Book")
                
                with col2:
                    if st.form_submit_button("Cancel"):
                        del st.session_state.edit_index
                
                if submitted:
                    if not title or not author or not pages:
                        st.error("Please fill in all required fields (marked with *)")
                    else:
                        update_book(index, title, author, isbn, genre, year, pages, 
                                   current_page, status, rating, review, cover_file)
                        del st.session_state.edit_index

def show_search_filters():
    with st.expander("Search & Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_query = st.text_input("Search by Title or Author")
            genre_filter = st.multiselect(
                "Filter by Genre",
                st.session_state.library_df['Genre'].unique().tolist()
            )
        
        with col2:
            status_filter = st.multiselect(
                "Filter by Status",
                ["Unread", "Reading", "Completed", "On Hold", "Dropped"],
                default=[]
            )
            year_min, year_max = st.slider(
                "Publication Year Range",
                min_value=int(st.session_state.library_df['Publication Year'].min()) if not st.session_state.library_df.empty else 0,
                max_value=int(st.session_state.library_df['Publication Year'].max()) if not st.session_state.library_df.empty else datetime.date.today().year,
                value=(0, datetime.date.today().year)
            )
        
        with col3:
            rating_filter = st.slider(
                "Minimum Rating",
                min_value=0,
                max_value=5,
                value=0
            )
            sort_option = st.selectbox(
                "Sort By",
                ["Date Added (Newest)", "Date Added (Oldest)", "Title (A-Z)", "Title (Z-A)", 
                 "Author (A-Z)", "Author (Z-A)", "Rating (High-Low)", "Rating (Low-High)"]
            )
    
    return {
        'search_query': search_query,
        'genre_filter': genre_filter,
        'status_filter': status_filter,
        'year_min': year_min,
        'year_max': year_max,
        'rating_filter': rating_filter,
        'sort_option': sort_option
    }

def filter_and_sort_books(filters):
    filtered_df = st.session_state.library_df.copy()
    
    # Apply filters
    if filters['search_query']:
        search = filters['search_query'].lower()
        filtered_df = filtered_df[
            filtered_df['Title'].str.lower().str.contains(search) |
            filtered_df['Author'].str.lower().str.contains(search)
        ]
    
    if filters['genre_filter']:
        filtered_df = filtered_df[filtered_df['Genre'].isin(filters['genre_filter'])]
    
    if filters['status_filter']:
        filtered_df = filtered_df[filtered_df['Status'].isin(filters['status_filter'])]
    
    filtered_df = filtered_df[
        (filtered_df['Publication Year'] >= filters['year_min']) &
        (filtered_df['Publication Year'] <= filters['year_max'])
    ]
    
    filtered_df = filtered_df[filtered_df['Rating'] >= filters['rating_filter']]
    
    # Apply sorting
    sort_mapping = {
        "Date Added (Newest)": ('Date Added', False),
        "Date Added (Oldest)": ('Date Added', True),
        "Title (A-Z)": ('Title', True),
        "Title (Z-A)": ('Title', False),
        "Author (A-Z)": ('Author', True),
        "Author (Z-A)": ('Author', False),
        "Rating (High-Low)": ('Rating', False),
        "Rating (Low-High)": ('Rating', True)
    }
    
    sort_column, ascending = sort_mapping.get(filters['sort_option'], ('Date Added', False))
    filtered_df = filtered_df.sort_values(by=sort_column, ascending=ascending)
    
    return filtered_df

def show_statistics():
    if st.session_state.library_df.empty:
        st.warning("No books in your library yet. Add some books to see statistics.")
        return
    
    st.subheader("Library Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Books", len(st.session_state.library_df))
        st.metric("Books Read", len(st.session_state.library_df[st.session_state.library_df['Status'] == 'Completed']))
    
    with col2:
        st.metric("Total Pages", int(st.session_state.library_df['Pages'].sum()))
        st.metric("Average Rating", f"{st.session_state.library_df['Rating'].mean():.1f}/5")
    
    with col3:
        read_pages = st.session_state.library_df[st.session_state.library_df['Status'] == 'Completed']['Pages'].sum()
        reading_pages = st.session_state.library_df[st.session_state.library_df['Status'] == 'Reading']['Current Page'].sum()
        st.metric("Pages Read", f"{read_pages + reading_pages:,}")
    
    st.divider()
    
    # Visualization section
    tab1, tab2, tab3, tab4 = st.tabs(["By Genre", "By Status", "By Year", "By Rating"])
    
    with tab1:
        if not st.session_state.library_df.empty:
            genre_counts = st.session_state.library_df['Genre'].value_counts().reset_index()
            genre_counts.columns = ['Genre', 'Count']
            fig = px.pie(genre_counts, values='Count', names='Genre', title='Books by Genre')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        if not st.session_state.library_df.empty:
            status_counts = st.session_state.library_df['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig = px.bar(status_counts, x='Status', y='Count', title='Books by Reading Status')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        if not st.session_state.library_df.empty:
            year_counts = st.session_state.library_df['Publication Year'].value_counts().sort_index().reset_index()
            year_counts.columns = ['Year', 'Count']
            fig = px.line(year_counts, x='Year', y='Count', title='Books by Publication Year')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        if not st.session_state.library_df.empty:
            rating_counts = st.session_state.library_df['Rating'].value_counts().sort_index().reset_index()
            rating_counts.columns = ['Rating', 'Count']
            fig = px.bar(rating_counts, x='Rating', y='Count', title='Books by Rating')
            st.plotly_chart(fig, use_container_width=True)

# Main App
def main():
    st.title("📚 My Personal Library")
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        app_mode = st.radio(
            "Go to",
            ["My Library", "Add Book", "Statistics"],
            index=0
        )
        
        st.divider()
        
        st.header("Quick Stats")
        if not st.session_state.library_df.empty:
            total_books = len(st.session_state.library_df)
            read_books = len(st.session_state.library_df[st.session_state.library_df['Status'] == 'Completed'])
            st.write(f"📖 **Total Books:** {total_books}")
            st.write(f"✅ **Books Read:** {read_books} ({read_books/total_books*100:.1f}%)")
            st.write(f"⭐ **Average Rating:** {st.session_state.library_df['Rating'].mean():.1f}/5")
        else:
            st.write("No books in your library yet.")
    
    # Main content based on navigation
    if app_mode == "My Library":
        if st.session_state.library_df.empty:
            st.info("Your library is empty. Add your first book using the 'Add Book' section!")
        else:
            filters = show_search_filters()
            filtered_books = filter_and_sort_books(filters)
            
            if filtered_books.empty:
                st.warning("No books match your filters.")
            else:
                st.write(f"Showing {len(filtered_books)} of {len(st.session_state.library_df)} books")
                
                # Display books in a responsive grid
                cols = st.columns(3)
                for index, (_, book) in enumerate(filtered_books.iterrows()):
                    with cols[index % 3]:
                        show_book_card(book, index)
                
                show_edit_book_form()
    
    elif app_mode == "Add Book":
        show_add_book_form()
    
    elif app_mode == "Statistics":
        show_statistics()

if __name__ == "__main__":
    main()