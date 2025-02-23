from flask_login import current_user
import json
from datetime import datetime

class SettingsManager:
    def __init__(self, db):
        self.db = db

    def get_default_settings(self):
        return {
            'display': {
                'default_chart_view': '1m',
                'default_scale': 'linear',
                'theme': 'dark'
            },
            'notifications': {
                'email_enabled': True,
                'browser_enabled': True,
                'frequency': 'realtime'
            },
            'data': {
                'moving_average': 0,
                'auto_refresh': 0
            },
            'last_updated': datetime.utcnow().isoformat()
        }

    def get_user_settings(self):
        if not current_user.is_authenticated:
            return self.get_default_settings()

        # Get settings from database
        settings = self.db.session.execute(
            'SELECT settings FROM user_settings WHERE user_id = :user_id',
            {'user_id': current_user.id}
        ).fetchone()

        if not settings:
            default_settings = self.get_default_settings()
            self.save_user_settings(default_settings)
            return default_settings

        return json.loads(settings[0])

    def save_user_settings(self, settings):
        if not current_user.is_authenticated:
            return False

        settings['last_updated'] = datetime.utcnow().isoformat()
        
        # Update or insert settings
        self.db.session.execute(
            '''
            INSERT INTO user_settings (user_id, settings) 
            VALUES (:user_id, :settings)
            ON CONFLICT (user_id) DO UPDATE 
            SET settings = :settings
            ''',
            {
                'user_id': current_user.id,
                'settings': json.dumps(settings)
            }
        )
        self.db.session.commit()
        return True 