
import streamlit as st
import json
from utils.feed_parser import FeedParser

# Configure Streamlit to run on 0.0.0.0:8501
st.set_page_config(page_title="AI Content Generator")
st.server.server.port = 8501
st.server.server.address = "0.0.0.0"
import os
from utils.content_generator import ContentGenerator
from utils.wordpress_api import WordPressAPI
from utils.seo_optimizer import SEOOptimizer
from utils.trend_analyzer import TrendAnalyzer
import time

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'feed_parser' not in st.session_state:
    st.session_state.feed_parser = FeedParser()
if 'content_generator' not in st.session_state:
    st.session_state.content_generator = ContentGenerator()
if 'seo_optimizer' not in st.session_state:
    st.session_state.seo_optimizer = SEOOptimizer()
if 'trend_analyzer' not in st.session_state:
    st.session_state.trend_analyzer = TrendAnalyzer()
if 'wordpress_api' not in st.session_state:
    st.session_state.wordpress_api = None
if 'feed_cache' not in st.session_state:
    st.session_state.feed_cache = {}
if 'content_cache' not in st.session_state:
    st.session_state.content_cache = {}
if 'site_config' not in st.session_state:
    st.session_state.site_config = {}
if 'generated_articles' not in st.session_state:
    st.session_state.generated_articles = []

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Site Management", "Bulk Article Generator"])
st.session_state.page = page.lower()

if st.session_state.page == "home":
    st.title("AI Content Generator")
    st.markdown("""
    Welcome to the AI Content Generator! This tool helps you:
    1. Generate SEO-optimized content from RSS feeds
    2. Analyze Google Trends
    3. Manage multiple WordPress sites
    4. Create bulk articles efficiently

    Get started by navigating to:
    - **Site Management** to configure your WordPress sites
    - **Bulk Article Generator** to create content
    """)

elif st.session_state.page == "site management":
    st.title("Site Management")

    # Display existing sites
    if st.session_state.site_config:
        st.header("Configured Sites")
        cols = st.columns(3)
        for i, (site_name, config) in enumerate(st.session_state.site_config.items()):
            with cols[i % 3]:
                if st.button(f"📝 {site_name}"):
                    st.session_state.selected_site = site_name

    # Display selected site details
    if 'selected_site' in st.session_state and st.session_state.selected_site:
        site = st.session_state.site_config[st.session_state.selected_site]
        st.subheader(f"Configuration: {st.session_state.selected_site}")

        with st.form("edit_site"):
            wp_url = st.text_input("WordPress URL", value=site.get('wp_url', ''))
            wp_username = st.text_input("Username", value=site.get('wp_username', ''))
            wp_password = st.text_input("Application Password", type="password")
            feed_urls = st.text_area("RSS Feed URLs (one per line)", 
                                   value='\n'.join(site.get('feed_urls', [])))

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Update"):
                    st.session_state.site_config[st.session_state.selected_site].update({
                        'wp_url': wp_url,
                        'wp_username': wp_username,
                        'wp_password': wp_password if wp_password else site.get('wp_password', ''),
                        'feed_urls': [url.strip() for url in feed_urls.split('\n') if url.strip()]
                    })
                    st.success("Site updated successfully!")

            with col2:
                if st.form_submit_button("Delete"):
                    del st.session_state.site_config[st.session_state.selected_site]
                    del st.session_state.selected_site
                    st.success("Site deleted successfully!")
                    st.rerun()

    # Add new site form
    st.header("Add New Site")
    site_name = st.text_input("Site Name")
    if site_name:
        if site_name not in st.session_state.site_config:
            st.session_state.site_config[site_name] = {}
            st.success(f"Site {site_name} added! Configure it above.")
            st.rerun()

elif st.session_state.page == "bulk article generator":
    st.title("Bulk Article Generator")

    # Site Selection
    if not st.session_state.site_config:
        st.warning("Please configure at least one site in Site Management first.")
    else:
        selected_site = st.selectbox("Select Site", list(st.session_state.site_config.keys()))
        config = st.session_state.site_config[selected_site]

        # Content Source Selection
        source_type = st.radio("Content Source", ["RSS Feeds", "Google Trends", "Custom Topics"])

        if source_type == "RSS Feeds":
            feed_source = st.radio("Feed Source", ["Saved Feeds", "Custom Feed"])
            if feed_source == "Saved Feeds":
                selected_feeds = st.multiselect("Select Feeds", config.get('feed_urls', []))
            else:
                custom_feed = st.text_input("Enter RSS Feed URL")
                selected_feeds = [custom_feed] if custom_feed else []

        elif source_type == "Google Trends":
            category = st.selectbox("Category", st.session_state.trend_analyzer.get_categories())
            trend_keywords = st.session_state.trend_analyzer.get_trending_topics(category)
            selected_topics = st.multiselect("Select Trending Topics", trend_keywords)

        else:  # Custom Topics
            custom_topics = st.text_area("Enter Topics (one per line)")
            selected_topics = [topic.strip() for topic in custom_topics.split('\n') if topic.strip()]

        # Language Selection
        target_language = st.selectbox("Target Language", ["English", "Hindi", "Spanish"])

        # Generation Settings
        with st.expander("Advanced Settings"):
            articles_per_topic = st.number_input("Articles per Topic", min_value=1, value=1)
            min_words = st.number_input("Minimum Words", min_value=300, value=600)
            include_images = st.checkbox("Include AI-generated Images", value=True)

        if st.button("Generate Articles"):
            with st.spinner("Generating articles..."):
                # Implementation for article generation...
                st.success("Articles generated successfully!")

        # Display Generated Articles
        if st.session_state.generated_articles:
            st.header("Generated Articles")
            for article in st.session_state.generated_articles:
                with st.expander(article['title']):
                    st.write(f"Status: {article['status']}")
                    st.write(f"Word Count: {article['word_count']}")
                    if st.button(f"View Full Content", key=article['id']):
                        st.write(article['content'])
