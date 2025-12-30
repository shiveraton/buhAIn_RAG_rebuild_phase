"""
Management command to populate the Baybayin Codex with sample articles.
Usage: python manage.py populate_sample_articles
"""

from django.core.management.base import BaseCommand
from baybayin_codex.models import CodexArticle, CodexCategory
from django.utils import timezone


class Command(BaseCommand):
    help = 'Populates the Baybayin Codex with sample articles about Baybayin script'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample Baybayin articles...'))
        
        # First, ensure categories exist
        categories_data = [
            {
                'name': 'Introduction',
                'description': 'Getting started with Baybayin',
                'icon': 'book-outline',
                'color': '#3880ff',
                'order': 1
            },
            {
                'name': 'Characters & Writing',
                'description': 'Learn Baybayin characters and writing system',
                'icon': 'create-outline',
                'color': '#10dc60',
                'order': 2
            },
            {
                'name': 'History & Culture',
                'description': 'Historical and cultural context of Baybayin',
                'icon': 'time-outline',
                'color': '#ffce00',
                'order': 3
            },
            {
                'name': 'Practice & Tutorials',
                'description': 'Hands-on practice and tutorials',
                'icon': 'school-outline',
                'color': '#f04141',
                'order': 4
            }
        ]
        
        categories = {}
        for cat_data in categories_data:
            cat, created = CodexCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            categories[cat_data['name']] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created category: {cat.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nNow creating articles...'))
        
        self.stdout.write(self.style.SUCCESS(f'\nNow creating articles...'))

        articles_data = [
            {
                'title': 'Introduction to Baybayin Script',
                'category': 'Introduction',
                'summary': 'Baybayin is a pre-colonial Philippine writing system that belongs to the Brahmic family of scripts. It was widely used in the Philippines before the Spanish colonization.',
                'content': '''
                <h2>What is Baybayin?</h2>
                <p>Baybayin (ᜊᜌ᜔ᜊᜌᜒᜈ᜔) is an ancient script used in the Philippines before Spanish colonization. 
                It is a member of the Brahmic family of scripts, which originated in India and spread throughout Southeast Asia.</p>
                
                <h3>Historical Background</h3>
                <p>The script was primarily used by the Tagalog people, though similar scripts existed among other ethnic groups. 
                Historical documents show that Baybayin was used for writing poetry, love letters, and official documents.</p>
                
                <h3>Modern Revival</h3>
                <p>In recent years, there has been a cultural movement to revive and preserve Baybayin as part of Filipino heritage. 
                The script is now taught in some schools and used in art, tattoos, and modern Filipino identity.</p>
                ''',
                'tags': ['introduction', 'history', 'script', 'culture'],
                'metadata': {'difficulty': 'beginner', 'reading_time': '3 min'}
            },
            {
                'title': 'Baybayin Characters and Structure',
                'category': 'Characters & Writing',
                'summary': 'Baybayin consists of 17 basic characters representing consonants with an inherent vowel "a". Vowel modifications are done using diacritical marks called kudlit.',
                'content': '''
                <h2>Character System</h2>
                <p>Baybayin is an abugida, meaning each character represents a consonant with an inherent vowel sound "a".</p>
                
                <h3>Basic Characters</h3>
                <ul>
                    <li>ᜊ (ba) - B sound with inherent 'a'</li>
                    <li>ᜃ (ka) - K sound with inherent 'a'</li>
                    <li>ᜇ (da) - D sound with inherent 'a'</li>
                    <li>ᜄ (ga) - G sound with inherent 'a'</li>
                    <li>ᜑ (ha) - H sound with inherent 'a'</li>
                </ul>
                
                <h3>Kudlit System</h3>
                <p>The kudlit is a diacritical mark used to modify the vowel sound:</p>
                <ul>
                    <li>No kudlit = "a" sound (e.g., ᜊ = ba)</li>
                    <li>Kudlit above = "e" or "i" sound (e.g., ᜊᜒ = bi)</li>
                    <li>Kudlit below = "o" or "u" sound (e.g., ᜊᜓ = bu)</li>
                </ul>
                
                <h3>Vowels</h3>
                <p>Three independent vowel characters exist:</p>
                <ul>
                    <li>ᜀ - A</li>
                    <li>ᜁ - E/I</li>
                    <li>ᜂ - O/U</li>
                </ul>
                ''',
                'tags': ['characters', 'kudlit', 'vowels', 'consonants', 'tutorial'],
                'metadata': {'difficulty': 'beginner', 'reading_time': '5 min'}
            },
            {
                'title': 'Writing Your Name in Baybayin',
                'category': 'Practice & Tutorials',
                'summary': 'Learn how to transliterate your name into Baybayin script using the character system and kudlit marks.',
                'content': '''
                <h2>How to Write Your Name</h2>
                <p>Transliterating names into Baybayin is a fun way to learn the script!</p>
                
                <h3>Step-by-Step Guide</h3>
                <ol>
                    <li><strong>Break down your name into syllables</strong><br>
                    Example: "Maria" → Ma-ri-a</li>
                    
                    <li><strong>Find the matching Baybayin characters</strong><br>
                    Ma = ᜋ<br>
                    Ri = ᜍᜒ (R with kudlit above)<br>
                    A = ᜀ</li>
                    
                    <li><strong>Combine them</strong><br>
                    Maria = ᜋᜍᜒᜀ</li>
                </ol>
                
                <h3>Common Names</h3>
                <ul>
                    <li>Juan = ᜑᜓᜀᜈ᜔</li>
                    <li>Jose = ᜑᜓᜐᜒ</li>
                    <li>Pedro = ᜉᜒᜇ᜔ᜍᜓ</li>
                    <li>Ana = ᜀᜈ</li>
                </ul>
                
                <h3>Tips</h3>
                <ul>
                    <li>Baybayin doesn't have specific characters for C, F, Q, V, X, Z</li>
                    <li>These are usually replaced with similar sounds</li>
                    <li>The virama (᜔) is used to remove the inherent vowel</li>
                </ul>
                ''',
                'tags': ['tutorial', 'names', 'transliteration', 'practice'],
                'metadata': {'difficulty': 'intermediate', 'reading_time': '4 min'}
            },
            {
                'title': 'History of Baybayin',
                'category': 'History & Culture',
                'summary': 'Explore the rich history of Baybayin from pre-colonial times through Spanish colonization to modern revival efforts.',
                'content': '''
                <h2>Pre-Colonial Era</h2>
                <p>Before the Spanish arrived in 1521, Baybayin was widely used throughout the Philippine archipelago. 
                Spanish chroniclers documented its use for writing on bamboo, leaves, and bark.</p>
                
                <h3>Spanish Colonial Period</h3>
                <p>When the Spanish colonized the Philippines, they gradually replaced Baybayin with the Latin alphabet. 
                By the late 1600s, the use of Baybayin had significantly declined, though it persisted in some communities.</p>
                
                <h3>Decline and Near-Extinction</h3>
                <p>By the 19th century, Baybayin had almost completely disappeared from common use. 
                It was primarily preserved in historical documents and some indigenous communities.</p>
                
                <h3>Modern Revival (20th-21st Century)</h3>
                <p>Starting in the 1990s, cultural activists and scholars began efforts to revive Baybayin:</p>
                <ul>
                    <li>1997: Baybayin was added to the Unicode Standard</li>
                    <li>2013: House Bill 1022 proposed making Baybayin the national writing system</li>
                    <li>2018: Republic Act No. 11094 (National Writing System Act) was signed into law</li>
                    <li>Present: Baybayin is taught in some schools and used in cultural events</li>
                </ul>
                
                <h3>Contemporary Use</h3>
                <p>Today, Baybayin is experiencing a cultural renaissance:</p>
                <ul>
                    <li>Used in Philippine peso banknotes</li>
                    <li>Popular in tattoos and artwork</li>
                    <li>Featured in government logos and documents</li>
                    <li>Taught as part of cultural heritage programs</li>
                </ul>
                ''',
                'tags': ['history', 'culture', 'revival', 'legislation'],
                'metadata': {'difficulty': 'intermediate', 'reading_time': '6 min'}
            },
            {
                'title': 'Baybayin vs Modern Filipino Alphabet',
                'category': 'Characters & Writing',
                'summary': 'Understanding the differences and similarities between Baybayin and the modern Filipino alphabet based on Latin script.',
                'content': '''
                <h2>Key Differences</h2>
                
                <h3>Script Type</h3>
                <ul>
                    <li><strong>Baybayin:</strong> Abugida (syllabic script where consonants have inherent vowels)</li>
                    <li><strong>Modern Filipino:</strong> Alphabet (each letter represents a single sound)</li>
                </ul>
                
                <h3>Number of Characters</h3>
                <ul>
                    <li><strong>Baybayin:</strong> 17 basic characters + 3 vowels</li>
                    <li><strong>Modern Filipino:</strong> 28 letters (including Ñ and Ng)</li>
                </ul>
                
                <h3>Writing Direction</h3>
                <ul>
                    <li><strong>Baybayin:</strong> Traditionally top-to-bottom, can also be left-to-right</li>
                    <li><strong>Modern Filipino:</strong> Always left-to-right</li>
                </ul>
                
                <h3>Sound Representation</h3>
                <p>Baybayin lacks direct equivalents for some sounds in modern Filipino:</p>
                <ul>
                    <li>C → K or S</li>
                    <li>F → P</li>
                    <li>J → H or D</li>
                    <li>Q → K</li>
                    <li>V → B</li>
                    <li>X → KS</li>
                    <li>Z → S</li>
                </ul>
                
                <h3>Similarities</h3>
                <ul>
                    <li>Both can represent all Filipino phonemes with adaptation</li>
                    <li>Both are used in the Philippines</li>
                    <li>Both are part of Filipino cultural identity</li>
                </ul>
                ''',
                'tags': ['comparison', 'alphabet', 'phonetics', 'education'],
                'metadata': {'difficulty': 'intermediate', 'reading_time': '4 min'}
            },
            {
                'title': 'Cultural Significance of Baybayin',
                'category': 'History & Culture',
                'summary': 'Baybayin represents Filipino cultural heritage and identity, serving as a symbol of pre-colonial civilization and modern cultural pride.',
                'content': '''
                <h2>Symbol of Identity</h2>
                <p>Baybayin has become a powerful symbol of Filipino identity and cultural pride, representing:</p>
                <ul>
                    <li>Pre-colonial civilization and literacy</li>
                    <li>Indigenous heritage and traditions</li>
                    <li>Cultural resistance and preservation</li>
                    <li>National pride and unity</li>
                </ul>
                
                <h3>In Modern Filipino Culture</h3>
                
                <h4>Art and Design</h4>
                <p>Baybayin is widely used in contemporary Filipino art:</p>
                <ul>
                    <li>Tattoos (especially the "Batok" tradition)</li>
                    <li>Calligraphy and typography</li>
                    <li>Graphic design and logos</li>
                    <li>Street art and murals</li>
                </ul>
                
                <h4>Official Use</h4>
                <ul>
                    <li>Philippine currency features Baybayin characters</li>
                    <li>Government seals and logos</li>
                    <li>Public signage in cultural sites</li>
                    <li>Official documents and certificates</li>
                </ul>
                
                <h4>Education and Advocacy</h4>
                <ul>
                    <li>Workshops and seminars on Baybayin</li>
                    <li>Social media campaigns (#Baybayin)</li>
                    <li>Cultural festivals and exhibitions</li>
                    <li>Academic research and publications</li>
                </ul>
                
                <h3>Legislative Recognition</h3>
                <p>The National Writing System Act (RA 11094) declared Baybayin as the national writing system, 
                mandating its use in government agencies and educational institutions.</p>
                
                <h3>Global Filipino Diaspora</h3>
                <p>Baybayin has become a way for overseas Filipinos to connect with their roots and express 
                their cultural identity, appearing in community events, clothing, and personal items worldwide.</p>
                ''',
                'tags': ['culture', 'identity', 'art', 'legislation', 'diaspora'],
                'metadata': {'difficulty': 'advanced', 'reading_time': '5 min'}
            }
        ]

        created_count = 0
        updated_count = 0

        for article_data in articles_data:
            category_name = article_data.pop('category')
            category = categories[category_name]
            
            article, created = CodexArticle.objects.update_or_create(
                title=article_data['title'],
                defaults={
                    **article_data,
                    'category': category,
                    'is_published': True,
                    'published_at': timezone.now()
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {article.title}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'⟳ Updated: {article.title}'))

        self.stdout.write(self.style.SUCCESS(f'\nDone! Created {created_count} articles, Updated {updated_count} articles.'))
        self.stdout.write(self.style.SUCCESS('The chat feature should now work with semantic search!'))
