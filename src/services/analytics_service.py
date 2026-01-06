"""
Analytics Service
Business logic for analytics and insights
"""

from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from src.data.database import get_stats, get_sales
from src.ui.components import render_page_header, render_section_header
from src.utils.helpers import get_low_stock_books, group_sales_by_bundle


def render_analytics_page():
    """Main analytics page."""
    render_page_header(
        "Business Analytics",
        "Insights into your sales performance and inventory health"
    )
    
    # Force fresh data
    stats = get_stats()
    all_sales = get_sales()
    grouped_sales = group_sales_by_bundle(all_sales)
    
    # Calculate metrics
    total_revenue = sum(s["total"] for s in grouped_sales)
    total_items = sum(s["qty"] for s in grouped_sales)
    total_profit = sum(s['profit'] for s in grouped_sales)
    num_transactions = len(grouped_sales)
    
    # Count unique bundles vs single sales
    bundles_count = len([s for s in grouped_sales if s['type'] == 'bundle'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Beautiful gradient metrics
    _render_metric_cards(total_revenue, total_profit, total_items, num_transactions, bundles_count)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Inventory status
    _render_inventory_status(stats)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        _render_platform_chart(stats)
    
    with col2:
        _render_timeline_chart(all_sales)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Insights
    col1, col2 = st.columns(2)
    
    with col1:
        _render_best_sellers(all_sales)
    
    with col2:
        _render_alerts(stats)


def _render_metric_cards(total_revenue, total_profit, total_items, num_transactions, bundles_count):
    """Render metric cards with gradients."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 25px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);">
                <h3 style="margin: 0; font-size: 32px;">💰</h3>
                <p style="margin: 8px 0; font-size: 13px; opacity: 0.95; font-weight: 600;">REVENUE</p>
                <h2 style="margin: 5px 0; font-size: 26px; font-weight: 700;">€{total_revenue:.2f}</h2>
                <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.9;">📦 {total_items} books • {bundles_count} bundles</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        margin_pct = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                        padding: 25px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 16px rgba(67, 233, 123, 0.3);">
                <h3 style="margin: 0; font-size: 32px;">📈</h3>
                <p style="margin: 8px 0; font-size: 13px; opacity: 0.95; font-weight: 600;">PROFIT</p>
                <h2 style="margin: 5px 0; font-size: 26px; font-weight: 700;">€{total_profit:.2f}</h2>
                <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.9;">Margin: {margin_pct:.1f}%</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        avg_books_per_order = total_items / num_transactions if num_transactions > 0 else 0
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                        padding: 25px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 16px rgba(250, 112, 154, 0.3);">
                <h3 style="margin: 0; font-size: 32px;">📚</h3>
                <p style="margin: 8px 0; font-size: 13px; opacity: 0.95; font-weight: 600;">BOOKS SOLD</p>
                <h2 style="margin: 5px 0; font-size: 26px; font-weight: 700;">{total_items}</h2>
                <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.9;">Avg: {avg_books_per_order:.1f} books/order</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        avg_order_value = total_revenue / num_transactions if num_transactions > 0 else 0
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                        padding: 25px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 16px rgba(79, 172, 254, 0.3);">
                <h3 style="margin: 0; font-size: 32px;">🧾</h3>
                <p style="margin: 8px 0; font-size: 13px; opacity: 0.95; font-weight: 600;">AVG ORDER</p>
                <h2 style="margin: 5px 0; font-size: 26px; font-weight: 700;">€{avg_order_value:.2f}</h2>
                <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.9;">Per transaction</p>
            </div>
            """,
            unsafe_allow_html=True
        )


def _render_inventory_status(stats):
    """Render inventory status metrics."""
    render_section_header("Inventory Status", "📦")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📚 Active", stats['active_count'])
    with col2:
        st.metric("🔴 Sold Out", stats['sold_count'])
    with col3:
        st.metric("📦 Total Stock", stats['total_stock'])


def _render_platform_chart(stats):
    """Render sales by platform chart."""
    render_section_header("Sales by Platform", "🛒")
    if stats['platform_sales']:
        platform_df = pd.DataFrame([
            {"Platform": k, "Revenue (€)": v} 
            for k, v in sorted(stats['platform_sales'].items(), key=lambda x: x[1], reverse=True)
        ])
        st.bar_chart(platform_df.set_index("Platform"), height=300)
    else:
        st.info("No sales data")


def _render_timeline_chart(all_sales):
    """Render interactive sales timeline with hover info."""
    render_section_header("Sales Timeline (Interactive)", "📅")
    
    if not all_sales:
        st.info("No sales data")
        return
    
    # Aggregate by date with orders and books count
    sales_by_date = {}
    for s in all_sales:
        # ✅ FIXED: Parse date properly
        try:
            date_str = s["date"]
            if '/' in date_str:
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            elif ' ' in date_str:
                date_obj = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
            else:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            
            date = date_obj.strftime("%Y-%m-%d")
        except:
            date = s["date"]
        
        if date not in sales_by_date:
            sales_by_date[date] = {"revenue": 0, "orders": set(), "books": 0}
        
        sales_by_date[date]["revenue"] += s["total"]
        sales_by_date[date]["orders"].add(s.get("bundle_id") or s["id"])
        sales_by_date[date]["books"] += s["qty"]
    
    # Convert to dataframe
    timeline_data = []
    for date, data in sorted(sales_by_date.items()):
        timeline_data.append({
            "Date": date,
            "Revenue (€)": data["revenue"],
            "Orders": len(data["orders"]),
            "Books Sold": data["books"]
        })
    
    timeline_df = pd.DataFrame(timeline_data)
    
    # Create interactive Plotly chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timeline_df["Date"],
        y=timeline_df["Revenue (€)"],
        mode='lines+markers',
        name='Revenue',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8),
        customdata=timeline_df[["Orders", "Books Sold"]],
        hovertemplate='<b>%{x}</b><br>' +
                      'Revenue: €%{y:.2f}<br>' +
                      'Orders: %{customdata[0]}<br>' +
                      'Books: %{customdata[1]}<br>' +
                      '<extra></extra>'
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=20, b=0),
        hovermode='x unified',
        xaxis_title="Date",
        yaxis_title="Revenue (€)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_best_sellers(all_sales):
    """Render best selling books."""
    render_section_header("Best Sellers", "🏆")
    
    if not all_sales:
        st.info("No sales to analyze")
        return
    
    book_sales = {}
    for s in all_sales:
        title = s["book_title"]
        book_sales[title] = book_sales.get(title, 0) + s["qty"]
    
    top_sellers = sorted(book_sales.items(), key=lambda x: x[1], reverse=True)[:5]
    
    for i, (title, qty) in enumerate(top_sellers, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📖"
        st.write(f"{medal} **{title[:30]}** - {qty} sold")


def _render_alerts(stats):
    """Render system alerts."""
    render_section_header("Alerts", "⚠️")
    
    alerts_count = 0
    
    # Low stock alerts
    low_stock = get_low_stock_books()
    if low_stock:
        alerts_count += 1
        
        # Nice warning box
        st.warning(f"📉 **{len(low_stock)} book(s)** with low stock")
        
        # Show details in expandable section
        with st.expander("📋 View Low Stock Books", expanded=True):
            for book in low_stock:
                stock_icon = "🟡" if book['stock'] == 2 else "🔴"
                st.markdown(f"{stock_icon} **{book['title']}** — {book['stock']} left")
                st.caption(f"   Author: {book['author']} • Buy: €{book['buy_price']:.2f} • Target: €{book['target_price']:.2f}")
                st.divider()
    
    # Below cost books
    if stats['low_margin_books']:
        alerts_count += 1
        
        st.error(f"💔 **{len(stats['low_margin_books'])} book(s)** priced below cost")
        
        with st.expander("📋 View Books Below Cost", expanded=True):
            for b in stats['low_margin_books']:
                loss = b['buy'] - b['target']
                st.markdown(f"⚠️ **{b['title']}**")
                st.caption(f"   Buy: €{b['buy']:.2f} • Target: €{b['target']:.2f} • Loss: €{loss:.2f}")
                st.divider()
    
    # All good message
    if alerts_count == 0:
        st.success("✅ All systems healthy!")
        st.caption("📦 Stock levels good • 💰 Pricing optimal")


def get_overview_stats() -> dict:
    """Get overview stats for home page."""
    stats = get_stats()
    
    # Get all sales
    all_sales = get_sales()
    
    # ✅ Calculate date range (last 7 days from today)
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    # Debug logging
    print(f"\n🔍 WEEKLY STATS DEBUG:")
    print(f"   Today: {today}")
    print(f"   Week ago: {week_ago}")
    print(f"   Total sales in DB: {len(all_sales)}")
    
    weekly_sales = []
    
    for s in all_sales:
        try:
            date_str = s['date']
            
            # ✅ Parse different date formats
            if '/' in date_str:
                sale_date = datetime.strptime(date_str, "%d/%m/%Y").date()
            elif ' ' in date_str:
                sale_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d").date()
            else:
                sale_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # ✅ FIXED: Only count sales within last 7 days AND not in future
            in_range = week_ago <= sale_date <= today
            
            if sale_date > today:
                print(f"   ⏭️  Sale {s['id']}: {date_str} → {sale_date} → FUTURE (excluded)")
            else:
                print(f"   {'✅' if in_range else '❌'} Sale {s['id']}: {date_str} → {sale_date} → {'IN RANGE' if in_range else 'TOO OLD'}")
            
            if in_range:
                weekly_sales.append(s)
                
        except Exception as e:
            print(f"   ⚠️ Date parse error for sale {s['id']}: {date_str} - {e}")
            continue
    
    # Calculate weekly revenue
    weekly_revenue = sum(s['total'] for s in weekly_sales)
    
    print(f"   📊 Result: {len(weekly_sales)} sales, €{weekly_revenue:.2f} revenue\n")
    
    return {
        'book_count': stats['book_count'],
        'active_count': stats['active_count'],
        'revenue': stats['revenue'],
        'profit': stats['profit'],
        'weekly_sales': len(weekly_sales),
        'weekly_revenue': weekly_revenue,
        'low_stock_count': len(get_low_stock_books())
    }