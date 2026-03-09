"""
Intelligence Engine for Eagle Carrier Chatbot
Analytics, scoring, and insights for carrier behavior
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class IntelligenceEngine:
    def __init__(self, database):
        """
        Initialize intelligence engine

        Args:
            database: Database instance
        """
        self.db = database

    # ===== CARRIER SCORING =====

    def calculate_carrier_score(self, carrier_id: int) -> Dict:
        """
        Calculate comprehensive carrier score

        Returns:
            {
                'total_score': 85,
                'engagement_score': 90,
                'responsiveness_score': 80,
                'booking_score': 85,
                'reliability_score': 90,
                'grade': 'A'
            }
        """
        carrier = self.db.get_carrier(carrier_id)
        if not carrier:
            return None

        # Engagement score (0-100)
        # Based on query frequency and recency
        engagement = self._calculate_engagement_score(carrier)

        # Responsiveness score (0-100)
        # Based on how quickly they respond (not yet tracked, placeholder)
        responsiveness = 75  # Default

        # Booking score (0-100)
        # Based on booking conversion rate
        booking = self._calculate_booking_score(carrier)

        # Reliability score (0-100)
        # Based on booking completion rate (future feature)
        reliability = 80  # Default

        # Total score (weighted average)
        total = (
            engagement * 0.3 +
            responsiveness * 0.2 +
            booking * 0.3 +
            reliability * 0.2
        )

        # Grade
        if total >= 90:
            grade = 'A+'
        elif total >= 80:
            grade = 'A'
        elif total >= 70:
            grade = 'B'
        elif total >= 60:
            grade = 'C'
        else:
            grade = 'D'

        return {
            'total_score': round(total, 1),
            'engagement_score': round(engagement, 1),
            'responsiveness_score': round(responsiveness, 1),
            'booking_score': round(booking, 1),
            'reliability_score': round(reliability, 1),
            'grade': grade
        }

    def _calculate_engagement_score(self, carrier: Dict) -> float:
        """Calculate engagement score (0-100)"""
        total_queries = carrier.get('total_queries', 0)
        last_active = carrier.get('last_active_date')

        # Frequency component (0-50 points)
        if total_queries >= 50:
            frequency = 50
        elif total_queries >= 20:
            frequency = 40
        elif total_queries >= 10:
            frequency = 30
        elif total_queries >= 5:
            frequency = 20
        else:
            frequency = total_queries * 4

        # Recency component (0-50 points)
        if last_active:
            try:
                last_date = datetime.fromisoformat(last_active)
                days_ago = (datetime.now() - last_date).days

                if days_ago <= 7:
                    recency = 50
                elif days_ago <= 14:
                    recency = 40
                elif days_ago <= 30:
                    recency = 30
                elif days_ago <= 60:
                    recency = 20
                else:
                    recency = 10
            except:
                recency = 25
        else:
            recency = 0

        return frequency + recency

    def _calculate_booking_score(self, carrier: Dict) -> float:
        """Calculate booking conversion score (0-100)"""
        total_queries = carrier.get('total_queries', 0)
        total_bookings = carrier.get('total_bookings', 0)

        if total_queries == 0:
            return 0

        # Conversion rate
        conversion_rate = (total_bookings / total_queries) * 100

        # Scale to 0-100 (10% conversion = 100 points)
        if conversion_rate >= 10:
            return 100
        else:
            return conversion_rate * 10

    # ===== CARRIER INSIGHTS =====

    def get_carrier_insights(self, carrier_id: int) -> Dict:
        """
        Get comprehensive insights about a carrier

        Returns:
            {
                'preferred_lanes': [{'lane': 'ATL-DAL', 'count': 15}],
                'preferred_equipment': [{'type': 'Dry Van', 'count': 20}],
                'peak_days': ['Monday', 'Tuesday'],
                'avg_rate_range': {'min': 2000, 'max': 3000},
                'booking_patterns': {...}
            }
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get carrier queries
        cursor.execute('''
            SELECT * FROM carrier_queries
            WHERE carrier_id = ?
            ORDER BY timestamp DESC
        ''', (carrier_id,))

        queries = [dict(row) for row in cursor.fetchall()]
        conn.close()

        if not queries:
            return {
                'preferred_lanes': [],
                'preferred_equipment': [],
                'peak_days': [],
                'avg_rate_range': None,
                'booking_patterns': {}
            }

        # Analyze preferred lanes
        lane_counts = {}
        for q in queries:
            origin = q.get('origin')
            destination = q.get('destination')
            if origin and destination:
                lane = f"{origin}-{destination}"
                lane_counts[lane] = lane_counts.get(lane, 0) + 1

        preferred_lanes = [
            {'lane': lane, 'count': count}
            for lane, count in sorted(lane_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # Analyze equipment preferences
        equipment_counts = {}
        for q in queries:
            equipment = q.get('equipment_type')
            if equipment:
                equipment_counts[equipment] = equipment_counts.get(equipment, 0) + 1

        preferred_equipment = [
            {'type': equip, 'count': count}
            for equip, count in sorted(equipment_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        # Analyze peak days
        day_counts = {}
        for q in queries:
            try:
                timestamp = datetime.fromisoformat(q.get('timestamp'))
                day = timestamp.strftime('%A')
                day_counts[day] = day_counts.get(day, 0) + 1
            except:
                pass

        peak_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_days = [day for day, count in peak_days]

        # Booking patterns
        booking_rate = self._get_booking_rate(carrier_id)

        return {
            'preferred_lanes': preferred_lanes,
            'preferred_equipment': preferred_equipment,
            'peak_days': peak_days,
            'avg_rate_range': None,  # Future: track rate preferences
            'booking_patterns': {
                'booking_rate': booking_rate,
                'total_queries': len(queries),
                'total_bookings': len([q for q in queries if q.get('intent') == 'book_load'])
            }
        }

    def _get_booking_rate(self, carrier_id: int) -> float:
        """Calculate booking rate for carrier"""
        carrier = self.db.get_carrier(carrier_id)
        if not carrier:
            return 0

        total_queries = carrier.get('total_queries', 0)
        total_bookings = carrier.get('total_bookings', 0)

        if total_queries == 0:
            return 0

        return round((total_bookings / total_queries) * 100, 1)

    # ===== HOT LANES =====

    def get_hot_lanes(self, days: int = 30, min_queries: int = 3) -> List[Dict]:
        """
        Get most searched lanes in the last N days

        Returns:
            [
                {'lane': 'ATL-DAL', 'query_count': 25, 'carrier_count': 8},
                ...
            ]
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        since_date = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute('''
            SELECT
                origin,
                destination,
                COUNT(*) as query_count,
                COUNT(DISTINCT carrier_id) as carrier_count
            FROM carrier_queries
            WHERE
                timestamp >= ?
                AND origin IS NOT NULL
                AND destination IS NOT NULL
            GROUP BY origin, destination
            HAVING query_count >= ?
            ORDER BY query_count DESC
            LIMIT 20
        ''', (since_date, min_queries))

        hot_lanes = []
        for row in cursor.fetchall():
            hot_lanes.append({
                'lane': f"{row['origin']}-{row['destination']}",
                'query_count': row['query_count'],
                'carrier_count': row['carrier_count']
            })

        conn.close()
        return hot_lanes

    # ===== TOP CARRIERS =====

    def get_top_carriers(self, limit: int = 10, sort_by: str = 'engagement') -> List[Dict]:
        """
        Get top carriers by various metrics

        Args:
            limit: Number of carriers to return
            sort_by: 'engagement' | 'queries' | 'bookings'

        Returns:
            List of carrier dictionaries with scores
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if sort_by == 'queries':
            order_by = 'total_queries DESC'
        elif sort_by == 'bookings':
            order_by = 'total_bookings DESC'
        else:
            order_by = 'engagement_score DESC'

        cursor.execute(f'''
            SELECT * FROM carriers
            ORDER BY {order_by}
            LIMIT ?
        ''', (limit,))

        carriers = []
        for row in cursor.fetchall():
            carrier = dict(row)
            # Add calculated score
            score = self.calculate_carrier_score(carrier['id'])
            carrier['score'] = score
            carriers.append(carrier)

        conn.close()
        return carriers

    # ===== OVERALL STATS =====

    def get_overall_stats(self) -> Dict:
        """
        Get overall platform statistics

        Returns:
            {
                'total_carriers': 150,
                'active_carriers_7d': 45,
                'total_queries': 1250,
                'total_bookings': 85,
                'avg_engagement_score': 65.5
            }
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Total carriers
        cursor.execute('SELECT COUNT(*) as count FROM carriers')
        total_carriers = cursor.fetchone()['count']

        # Active carriers (last 7 days)
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute('''
            SELECT COUNT(*) as count FROM carriers
            WHERE last_active_date >= ?
        ''', (seven_days_ago,))
        active_carriers_7d = cursor.fetchone()['count']

        # Total queries
        cursor.execute('SELECT COUNT(*) as count FROM carrier_queries')
        total_queries = cursor.fetchone()['count']

        # Total bookings
        cursor.execute('SELECT COUNT(*) as count FROM booking_requests')
        total_bookings = cursor.fetchone()['count']

        # Average engagement score
        cursor.execute('SELECT AVG(engagement_score) as avg FROM carriers')
        avg_engagement = cursor.fetchone()['avg'] or 0

        conn.close()

        return {
            'total_carriers': total_carriers,
            'active_carriers_7d': active_carriers_7d,
            'total_queries': total_queries,
            'total_bookings': total_bookings,
            'avg_engagement_score': round(avg_engagement, 1)
        }

    # ===== RECENT ACTIVITY =====

    def get_recent_queries(self, limit: int = 20) -> List[Dict]:
        """Get recent carrier queries with carrier info"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                cq.*,
                c.name as carrier_name,
                c.phone as carrier_phone
            FROM carrier_queries cq
            LEFT JOIN carriers c ON cq.carrier_id = c.id
            ORDER BY cq.timestamp DESC
            LIMIT ?
        ''', (limit,))

        queries = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return queries

    def get_carrier_history(self, carrier_id: int, days: int = 90) -> List[Dict]:
        """Get carrier query history"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        since_date = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute('''
            SELECT * FROM carrier_queries
            WHERE carrier_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        ''', (carrier_id, since_date))

        history = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return history

    # ===== ANALYTICS =====

    def get_daily_activity(self, days: int = 30) -> List[Dict]:
        """Get daily query counts for the last N days"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        since_date = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute('''
            SELECT
                DATE(timestamp) as date,
                COUNT(*) as query_count,
                COUNT(DISTINCT carrier_id) as carrier_count
            FROM carrier_queries
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date ASC
        ''', (since_date,))

        activity = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return activity

    def get_equipment_breakdown(self) -> List[Dict]:
        """Get query breakdown by equipment type"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                equipment_type,
                COUNT(*) as query_count
            FROM carrier_queries
            WHERE equipment_type IS NOT NULL
            GROUP BY equipment_type
            ORDER BY query_count DESC
        ''', ())

        breakdown = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return breakdown

    def get_geography_stats(self) -> Dict:
        """Get statistics by origin/destination"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Top origins
        cursor.execute('''
            SELECT origin, COUNT(*) as count
            FROM carrier_queries
            WHERE origin IS NOT NULL
            GROUP BY origin
            ORDER BY count DESC
            LIMIT 10
        ''')
        top_origins = [dict(row) for row in cursor.fetchall()]

        # Top destinations
        cursor.execute('''
            SELECT destination, COUNT(*) as count
            FROM carrier_queries
            WHERE destination IS NOT NULL
            GROUP BY destination
            ORDER BY count DESC
            LIMIT 10
        ''')
        top_destinations = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            'top_origins': top_origins,
            'top_destinations': top_destinations
        }

    # ===== RECOMMENDATIONS =====

    def recommend_carriers_for_load(self, origin: str, destination: str,
                                    equipment_type: str = None,
                                    limit: int = 10) -> List[Dict]:
        """
        Recommend best carriers for a specific load based on intelligence

        Returns:
            List of carriers sorted by relevance score
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Find carriers who have searched this lane or similar
        query = '''
            SELECT
                c.*,
                COUNT(cq.id) as lane_familiarity,
                MAX(cq.timestamp) as last_lane_search
            FROM carriers c
            LEFT JOIN carrier_queries cq ON c.id = cq.carrier_id
                AND (cq.origin = ? OR cq.destination = ?)
        '''

        params = [origin, destination]

        if equipment_type:
            query += ' AND cq.equipment_type = ?'
            params.append(equipment_type)

        query += '''
            GROUP BY c.id
            ORDER BY lane_familiarity DESC, c.engagement_score DESC
            LIMIT ?
        '''
        params.append(limit)

        cursor.execute(query, params)

        recommendations = []
        for row in cursor.fetchall():
            carrier = dict(row)
            score = self.calculate_carrier_score(carrier['id'])
            carrier['score'] = score
            carrier['recommendation_score'] = carrier['lane_familiarity'] * 10 + (score['total_score'] if score else 0)
            recommendations.append(carrier)

        conn.close()

        # Sort by recommendation score
        recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)

        return recommendations
