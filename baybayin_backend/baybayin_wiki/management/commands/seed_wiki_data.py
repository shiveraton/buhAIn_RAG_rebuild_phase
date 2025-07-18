"""
Seed data for BaybayinWiki

This file contains comprehensive content for the Baybayin Wiki, including:
- Historical information
- Cultural significance
- Technical aspects
- Modern applications
- Interactive examples
"""

from django.core.management.base import BaseCommand
from baybayin_wiki.models import WikiCategory, WikiArticle, WikiTimeline, WikiGlossary
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Seed the database with Baybayin Wiki content'

    def handle(self, *args, **options):
        # Create superuser if doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')

        # Create categories
        categories_data = [
            {
                'name': 'History & Origins',
                'description': 'The historical development and origins of Baybayin script',
                'icon': 'library-outline',
                'color': '#8B4513',
                'order': 1
            },
            {
                'name': 'Script & Characters',
                'description': 'Learn about Baybayin characters, rules, and writing system',
                'icon': 'text-outline',
                'color': '#FF6B35',
                'order': 2
            },
            {
                'name': 'Cultural Significance',
                'description': 'Cultural importance and role in Filipino identity',
                'icon': 'heart-outline',
                'color': '#C41E3A',
                'order': 3
            },
            {
                'name': 'Modern Applications',
                'description': 'Contemporary uses and revival of Baybayin',
                'icon': 'phone-portrait-outline',
                'color': '#2E8B57',
                'order': 4
            },
            {
                'name': 'Regional Variations',
                'description': 'Different scripts across Philippine regions',
                'icon': 'location-outline',
                'color': '#4169E1',
                'order': 5
            },
            {
                'name': 'Learning Resources',
                'description': 'Guides, tutorials, and practice materials',
                'icon': 'school-outline',
                'color': '#FF1493',
                'order': 6
            }
        ]

        for cat_data in categories_data:
            category, created = WikiCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f"Created category: {category.name}")

        # Create articles
        self.create_articles()
        
        # Create timeline events
        self.create_timeline()
        
        # Create glossary terms
        self.create_glossary()
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded BaybayinWiki data'))

    def create_articles(self):
        """Create comprehensive wiki articles"""
        
        # Get categories
        history_cat = WikiCategory.objects.get(name='History & Origins')
        script_cat = WikiCategory.objects.get(name='Script & Characters')
        cultural_cat = WikiCategory.objects.get(name='Cultural Significance')
        modern_cat = WikiCategory.objects.get(name='Modern Applications')
        regional_cat = WikiCategory.objects.get(name='Regional Variations')
        learning_cat = WikiCategory.objects.get(name='Learning Resources')
        
        articles_data = [
            {
                'title': 'Origins of Baybayin: The Ancient Filipino Script',
                'category': history_cat,
                'summary': 'Discover the fascinating origins of Baybayin, from its Indian Brahmi roots to its development in the Philippine archipelago.',
                'content': '''
                <h2>The Ancient Roots</h2>
                <p>Baybayin, the ancient script of the Philippines, traces its origins to the Brahmi script of ancient India. This writing system arrived in the archipelago through trade routes and cultural exchanges that connected Southeast Asia with the Indian subcontinent.</p>
                
                <h3>Archaeological Evidence</h3>
                <p>The earliest evidence of Baybayin dates back to the 13th century, found in artifacts such as the Laguna Copperplate Inscription (LCI) from 900 CE, which contains a mix of Sanskrit, Old Malay, and Old Javanese written in Kawi script—a precursor to Baybayin.</p>
                
                <h3>Evolution and Development</h3>
                <p>Over centuries, the script evolved and adapted to local languages and phonetic needs. Different regions developed their own variations, reflecting the linguistic diversity of the Philippines.</p>
                
                <h3>Pre-colonial Literacy</h3>
                <p>Contrary to colonial narratives, the Philippines had a thriving literate culture before European contact. Spanish chroniclers like Miguel López de Legazpi noted that most inhabitants could read and write in their native script.</p>
                
                <h3>The Name "Baybayin"</h3>
                <p>The term "Baybayin" comes from the Tagalog word "baybay," meaning "to spell" or "to write." It was also historically known as "Alibata," though this term is now considered outdated and inaccurate.</p>
                ''',
                'featured_image': 'assets/wiki/baybayin-origins.jpg',
                'baybayin_examples': [
                    {
                        'text': 'ᜊᜌ᜔ᜊᜌᜒᜈ᜔',
                        'translation': 'Baybayin',
                        'description': 'The word "Baybayin" written in its own script'
                    }
                ],
                'tags': ['history', 'origins', 'ancient', 'philippines', 'brahmi'],
                'reading_time': 8,
                'difficulty_level': 'beginner',
                'is_featured': True,
                'keywords': 'Baybayin origins, ancient Filipino script, Brahmi script, Philippine history'
            },
            {
                'title': 'The Spanish Colonial Impact on Baybayin',
                'category': history_cat,
                'summary': 'Learn how Spanish colonization affected the use and preservation of Baybayin script in the Philippines.',
                'content': '''
                <h2>The Colonial Encounter</h2>
                <p>When Spanish colonizers arrived in the Philippines in the 16th century, they encountered a literate society that used Baybayin for various purposes including trade, communication, and literature.</p>
                
                <h3>Initial Documentation</h3>
                <p>Spanish missionaries and chroniclers documented Baybayin extensively. Notable figures like Francisco López documented the script in their works, providing valuable historical records.</p>
                
                <h3>The Shift to Latin Script</h3>
                <p>As Spanish colonial rule intensified, the Latin alphabet was promoted for official documents, religious texts, and education. This gradual shift led to the decline of Baybayin usage in many areas.</p>
                
                <h3>Missionary Adaptations</h3>
                <p>Some Spanish missionaries attempted to use Baybayin for religious instruction, creating hybrid texts that combined Latin and Baybayin scripts. However, these efforts were limited and eventually abandoned.</p>
                
                <h3>Resistance and Preservation</h3>
                <p>Despite colonial pressures, some communities continued to use Baybayin, particularly in remote areas. The script survived in various forms, preserved by indigenous communities and local scholars.</p>
                ''',
                'featured_image': 'assets/wiki/spanish-colonial-impact.jpg',
                'tags': ['spanish', 'colonial', 'missionaries', 'latin', 'decline'],
                'reading_time': 7,
                'difficulty_level': 'intermediate',
                'keywords': 'Spanish colonization, Baybayin decline, colonial impact, missionary work'
            },
            {
                'title': 'The 17 Characters of Baybayin',
                'category': script_cat,
                'summary': 'A comprehensive guide to the 17 basic characters of Baybayin: 3 vowels and 14 consonants.',
                'content': '''
                <h2>The Baybayin Character Set</h2>
                <p>Baybayin consists of 17 fundamental characters that form the foundation of the writing system. Understanding these characters is essential for learning to read and write in Baybayin.</p>
                
                <h3>The Three Vowels</h3>
                <p>Baybayin has three basic vowel sounds, each represented by a unique character:</p>
                <ul>
                    <li><strong>A (ᜀ)</strong> - The fundamental vowel sound</li>
                    <li><strong>E/I (ᜁ)</strong> - Represents both 'e' and 'i' sounds</li>
                    <li><strong>O/U (ᜂ)</strong> - Represents both 'o' and 'u' sounds</li>
                </ul>
                
                <h3>The Fourteen Consonants</h3>
                <p>Each consonant character has an inherent 'a' sound that can be modified with kudlit (diacritical marks):</p>
                <ul>
                    <li><strong>Ba (ᜊ)</strong> - The 'ba' sound</li>
                    <li><strong>Ka (ᜃ)</strong> - The 'ka' sound</li>
                    <li><strong>Da (ᜇ)</strong> - The 'da' sound</li>
                    <li><strong>Ga (ᜄ)</strong> - The 'ga' sound</li>
                    <li><strong>Ha (ᜑ)</strong> - The 'ha' sound</li>
                    <li><strong>La (ᜎ)</strong> - The 'la' sound</li>
                    <li><strong>Ma (ᜋ)</strong> - The 'ma' sound</li>
                    <li><strong>Na (ᜈ)</strong> - The 'na' sound</li>
                    <li><strong>Nga (ᜅ)</strong> - The 'nga' sound</li>
                    <li><strong>Pa (ᜉ)</strong> - The 'pa' sound</li>
                    <li><strong>Ra (ᜇ)</strong> - The 'ra' sound</li>
                    <li><strong>Sa (ᜐ)</strong> - The 'sa' sound</li>
                    <li><strong>Ta (ᜆ)</strong> - The 'ta' sound</li>
                    <li><strong>Wa (ᜏ)</strong> - The 'wa' sound</li>
                    <li><strong>Ya (ᜌ)</strong> - The 'ya' sound</li>
                </ul>
                
                <h3>The Kudlit System</h3>
                <p>Kudlit are small marks placed above or below consonant characters to change their vowel sound:</p>
                <ul>
                    <li><strong>Kudlit above (◌᜔)</strong> - Changes 'a' to 'e' or 'i'</li>
                    <li><strong>Kudlit below (◌᜕)</strong> - Changes 'a' to 'o' or 'u'</li>
                </ul>
                ''',
                'featured_image': 'assets/wiki/baybayin-characters.jpg',
                'baybayin_examples': [
                    {
                        'text': 'ᜀᜁᜂ',
                        'translation': 'A I/E O/U',
                        'description': 'The three basic vowels'
                    },
                    {
                        'text': 'ᜊᜒᜊᜓ',
                        'translation': 'Bi Bu',
                        'description': 'Examples of kudlit usage'
                    }
                ],
                'tags': ['characters', 'vowels', 'consonants', 'kudlit', 'alphabet'],
                'reading_time': 10,
                'difficulty_level': 'beginner',
                'is_featured': True,
                'keywords': 'Baybayin characters, vowels, consonants, kudlit, alphabet'
            },
            {
                'title': 'Baybayin in Modern Filipino Culture',
                'category': cultural_cat,
                'summary': 'Explore how Baybayin continues to influence modern Filipino culture, art, and identity.',
                'content': '''
                <h2>A Symbol of Filipino Identity</h2>
                <p>In contemporary Philippines, Baybayin has experienced a remarkable revival, becoming a powerful symbol of Filipino identity and cultural pride.</p>
                
                <h3>Government Recognition</h3>
                <p>The Philippine government has officially recognized Baybayin's importance:</p>
                <ul>
                    <li>Featured on the ₱1000 peso bill</li>
                    <li>Included in the national seal</li>
                    <li>Mandated for government signage in some areas</li>
                    <li>Taught in some public schools</li>
                </ul>
                
                <h3>Artistic Expression</h3>
                <p>Contemporary Filipino artists use Baybayin in various mediums:</p>
                <ul>
                    <li>Tattoo art and body modification</li>
                    <li>Calligraphy and typography</li>
                    <li>Digital art and graphic design</li>
                    <li>Fashion and jewelry design</li>
                    <li>Street art and murals</li>
                </ul>
                
                <h3>Cultural Movements</h3>
                <p>Various cultural movements have embraced Baybayin:</p>
                <ul>
                    <li>Educational advocacy groups</li>
                    <li>Cultural preservation societies</li>
                    <li>Filipino diaspora communities</li>
                    <li>Indigenous rights movements</li>
                </ul>
                
                <h3>Digital Age Adaptation</h3>
                <p>Baybayin has adapted to the digital age with:</p>
                <ul>
                    <li>Unicode standard inclusion</li>
                    <li>Mobile keyboards and apps</li>
                    <li>Social media usage</li>
                    <li>Online learning platforms</li>
                </ul>
                ''',
                'featured_image': 'assets/wiki/modern-baybayin.jpg',
                'baybayin_examples': [
                    {
                        'text': 'ᜉᜒᜎᜒᜉᜒᜈᜐ᜔',
                        'translation': 'Pilipinas',
                        'description': 'Philippines written in Baybayin'
                    }
                ],
                'tags': ['modern', 'culture', 'identity', 'art', 'government', 'digital'],
                'reading_time': 9,
                'difficulty_level': 'intermediate',
                'is_featured': True,
                'keywords': 'modern Baybayin, Filipino culture, cultural identity, contemporary art'
            },
            {
                'title': 'Learning to Write Baybayin: A Beginner\'s Guide',
                'category': learning_cat,
                'summary': 'Step-by-step instructions for learning to write Baybayin, including proper stroke order and techniques.',
                'content': '''
                <h2>Getting Started with Baybayin Writing</h2>
                <p>Learning to write Baybayin is an exciting journey that connects you with centuries of Filipino heritage. This guide will help you master the basics.</p>
                
                <h3>Writing Materials</h3>
                <p>You can practice Baybayin with simple materials:</p>
                <ul>
                    <li>Pen or pencil</li>
                    <li>Paper or practice notebooks</li>
                    <li>Bamboo pen (traditional)</li>
                    <li>Digital tablets and styluses</li>
                </ul>
                
                <h3>Basic Principles</h3>
                <p>Keep these principles in mind:</p>
                <ul>
                    <li>Write from left to right</li>
                    <li>Characters should be evenly spaced</li>
                    <li>Maintain consistent size and proportion</li>
                    <li>Practice smooth, flowing strokes</li>
                </ul>
                
                <h3>Stroke Order Basics</h3>
                <p>Most Baybayin characters follow these patterns:</p>
                <ul>
                    <li>Start from the top</li>
                    <li>Move from left to right</li>
                    <li>Complete main strokes before adding details</li>
                    <li>Add kudlit marks last</li>
                </ul>
                
                <h3>Practice Exercises</h3>
                <ol>
                    <li><strong>Vowel Practice</strong>: Start with the three basic vowels (ᜀ ᜁ ᜂ)</li>
                    <li><strong>Simple Consonants</strong>: Practice basic consonants like ᜊ ᜃ ᜇ</li>
                    <li><strong>Kudlit Practice</strong>: Add kudlit marks to change vowel sounds</li>
                    <li><strong>Word Formation</strong>: Combine characters to form simple words</li>
                    <li><strong>Sentence Writing</strong>: Progress to writing complete sentences</li>
                </ol>
                
                <h3>Common Mistakes to Avoid</h3>
                <ul>
                    <li>Inconsistent character sizing</li>
                    <li>Improper kudlit placement</li>
                    <li>Rushing through stroke order</li>
                    <li>Ignoring proper spacing</li>
                </ul>
                ''',
                'featured_image': 'assets/wiki/writing-guide.jpg',
                'interactive_elements': {
                    'practice_mode': True,
                    'stroke_animation': True,
                    'tracing_exercises': [
                        {'character': 'ᜀ', 'strokes': 2},
                        {'character': 'ᜊ', 'strokes': 3},
                        {'character': 'ᜃ', 'strokes': 2}
                    ]
                },
                'tags': ['learning', 'writing', 'beginner', 'tutorial', 'practice'],
                'reading_time': 12,
                'difficulty_level': 'beginner',
                'is_featured': True,
                'keywords': 'learn Baybayin, writing guide, stroke order, practice exercises'
            }
        ]
        
        for article_data in articles_data:
            article, created = WikiArticle.objects.get_or_create(
                title=article_data['title'],
                defaults=article_data
            )
            if created:
                self.stdout.write(f"Created article: {article.title}")

    def create_timeline(self):
        """Create historical timeline events"""
        timeline_data = [
            {
                'title': 'Laguna Copperplate Inscription',
                'year': 900,
                'period': 'Pre-colonial',
                'description': 'The earliest known written document in the Philippines, containing Sanskrit, Old Malay, and Old Javanese text in Kawi script.',
                'importance': 'critical'
            },
            {
                'title': 'Development of Baybayin',
                'year': 1300,
                'period': 'Pre-colonial',
                'description': 'Baybayin script fully develops from earlier Brahmic scripts, becoming widely used across the archipelago.',
                'importance': 'high'
            },
            {
                'title': 'Spanish Arrival',
                'year': 1521,
                'period': 'Colonial',
                'description': 'Spanish colonizers arrive and encounter a literate society using Baybayin for trade and communication.',
                'importance': 'high'
            },
            {
                'title': 'Doctrina Cristiana',
                'year': 1593,
                'period': 'Colonial',
                'description': 'First printed book in the Philippines, containing both Baybayin and Latin scripts.',
                'importance': 'high'
            },
            {
                'title': 'Paul Versoza\'s Research',
                'year': 1914,
                'period': 'American',
                'description': 'Extensive documentation and research on Baybayin by American anthropologist Paul Versoza.',
                'importance': 'medium'
            },
            {
                'title': 'Cultural Revival Movement',
                'year': 1960,
                'period': 'Modern',
                'description': 'Beginning of modern Baybayin revival movement with increased academic interest.',
                'importance': 'medium'
            },
            {
                'title': 'Unicode Standard Inclusion',
                'year': 2009,
                'period': 'Digital',
                'description': 'Baybayin characters officially included in Unicode standard, enabling digital usage.',
                'importance': 'high'
            },
            {
                'title': 'National Writing System Act',
                'year': 2018,
                'period': 'Contemporary',
                'description': 'Philippine Congress passes law declaring Baybayin as national writing system.',
                'importance': 'critical'
            }
        ]
        
        for event_data in timeline_data:
            event, created = WikiTimeline.objects.get_or_create(
                title=event_data['title'],
                year=event_data['year'],
                defaults=event_data
            )
            if created:
                self.stdout.write(f"Created timeline event: {event.title}")

    def create_glossary(self):
        """Create glossary terms"""
        glossary_data = [
            {
                'term': 'Baybayin',
                'pronunciation': 'bah-ee-bah-yin',
                'definition': 'The ancient script of the Philippines, derived from the Brahmi script of India.',
                'baybayin_script': 'ᜊᜌ᜔ᜊᜌᜒᜈ᜔',
                'category': 'script'
            },
            {
                'term': 'Kudlit',
                'pronunciation': 'kood-lit',
                'definition': 'Diacritical marks used to change the vowel sound of consonant characters.',
                'baybayin_script': 'ᜃᜓᜇ᜔ᜎᜒᜆ᜔',
                'category': 'grammar'
            },
            {
                'term': 'Alibata',
                'pronunciation': 'ah-lee-bah-tah',
                'definition': 'Outdated and inaccurate term for Baybayin, coined in the 1920s.',
                'baybayin_script': 'ᜀᜎᜒᜊᜆ',
                'category': 'terminology'
            },
            {
                'term': 'Virama',
                'pronunciation': 'vee-rah-mah',
                'definition': 'A mark used to cancel the inherent vowel sound of a consonant.',
                'baybayin_script': 'ᜊᜒᜇᜋ',
                'category': 'grammar'
            },
            {
                'term': 'Brahmi',
                'pronunciation': 'brah-mee',
                'definition': 'Ancient Indian script from which Baybayin and other Southeast Asian scripts derive.',
                'category': 'history'
            },
            {
                'term': 'Kawi',
                'pronunciation': 'kah-wee',
                'definition': 'Ancient script used in Java and other parts of Southeast Asia, precursor to Baybayin.',
                'category': 'history'
            },
            {
                'term': 'Sulat',
                'pronunciation': 'soo-laht',
                'definition': 'Tagalog word meaning "to write" or "writing".',
                'baybayin_script': 'ᜐᜓᜎᜆ᜔',
                'category': 'language'
            },
            {
                'term': 'Hanunoo',
                'pronunciation': 'hah-noo-noh-oh',
                'definition': 'Indigenous script of the Hanunoo people of Mindoro, related to Baybayin.',
                'category': 'regional'
            },
            {
                'term': 'Buhid',
                'pronunciation': 'boo-heed',
                'definition': 'Indigenous script of the Buhid people of Mindoro.',
                'category': 'regional'
            },
            {
                'term': 'Tagbanwa',
                'pronunciation': 'tahg-bahn-wah',
                'definition': 'Indigenous script of the Tagbanwa people of Palawan.',
                'category': 'regional'
            }
        ]
        
        for term_data in glossary_data:
            term, created = WikiGlossary.objects.get_or_create(
                term=term_data['term'],
                defaults=term_data
            )
            if created:
                self.stdout.write(f"Created glossary term: {term.term}")
