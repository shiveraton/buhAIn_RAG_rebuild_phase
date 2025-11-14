import { Component, OnInit } from '@angular/core';
import { AlertController } from '@ionic/angular';
import { 
  BaybayinWikiService, 
  WikiArticle, 
  SemanticSearchResult, 
  RelatedArticle 
} from './baybayin-wiki.service';

@Component({
  selector: 'app-baybayin-info',
  templateUrl: 'baybayin-info.page.html',
  styleUrls: ['baybayin-info.page.scss'],
  standalone: false,
})
export class BaybayinInfoPage implements OnInit {
  articles: WikiArticle[] = [];
  loading = true;
  error: string | null = null;

  // --- Semantic Search Properties ---
  searchQuery: string = '';
  searchResults: SemanticSearchResult[] = [];
  searchLoading = false;
  searchError: string | null = null;

  // --- Related Articles Properties ---
  selectedArticleId: number | null = null;
  relatedArticles: RelatedArticle[] = [];
  relatedLoading = false;

  // --- Chat Interface Properties ---
  chatMessages: Array<{role: 'user' | 'assistant', content: string}> = [];
  chatInput: string = '';
  chatLoading = false;

  // --- Tag Filter Properties ---
  availableTags: string[] = [];
  selectedTag: string | null = null;
  filteredArticles: WikiArticle[] = [];

  // --- Kudlit Playground Properties ---
  activeKudlitChar: string = 'ᜊ';
  activeLatinChar: string = 'Ba';
  currentVowel: 'a' | 'e/i' | 'o/u' = 'a';
  private kudlitMap = {
    'a': { baybayin: 'ᜊ', latin: 'a' },
    'e/i': { baybayin: 'ᜊᜒ', latin: 'i' },
    'o/u': { baybayin: 'ᜊᜓ', latin: 'u' }
  };

  // --- Wiki Menu State ---
  wikiMenuOpen: boolean = false;
  selectedWikiSection: string = 'articles';

  constructor(
    private baybayinWikiService: BaybayinWikiService,
    private alertController: AlertController
  ) {}

  ngOnInit() {
    this.loadArticles();
    this.loadTags();
  }

  loadArticles() {
    this.baybayinWikiService.getBaybayinArticles().subscribe({
      next: (data) => {
        this.articles = data;
        this.filteredArticles = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load Baybayin articles.';
        this.loading = false;
      }
    });
  }

  loadTags() {
    this.baybayinWikiService.getArticleTags().subscribe({
      next: (tags) => {
        this.availableTags = tags;
      },
      error: (err) => {
        console.error('Failed to load tags:', err);
      }
    });
  }

  // --- Semantic Search Methods ---
  performSemanticSearch() {
    if (!this.searchQuery.trim()) {
      this.searchResults = [];
      return;
    }

    this.searchLoading = true;
    this.searchError = null;

    this.baybayinWikiService.semanticSearch(this.searchQuery, 5).subscribe({
      next: (results) => {
        this.searchResults = results;
        this.searchLoading = false;
      },
      error: (err) => {
        this.searchError = 'Failed to perform search. Please try again.';
        this.searchLoading = false;
        console.error('Search error:', err);
      }
    });
  }

  clearSearch() {
    this.searchQuery = '';
    this.searchResults = [];
    this.searchError = null;
  }

  // --- Related Articles Methods ---
  loadRelatedArticles(articleId: number) {
    this.selectedArticleId = articleId;
    this.relatedLoading = true;

    this.baybayinWikiService.getRelatedArticles(articleId, 3).subscribe({
      next: (related) => {
        this.relatedArticles = related;
        this.relatedLoading = false;
      },
      error: (err) => {
        console.error('Failed to load related articles:', err);
        this.relatedLoading = false;
      }
    });
  }

  // --- Chat Interface Methods ---
  sendChatMessage() {
    if (!this.chatInput.trim()) {
      return;
    }

    const userMessage = this.chatInput.trim();
    this.chatMessages.push({ role: 'user', content: userMessage });
    this.chatInput = '';
    this.chatLoading = true;

    // Use semantic search as the "chat" backend
    this.baybayinWikiService.semanticSearch(userMessage, 3).subscribe({
      next: (results) => {
        if (results.length > 0) {
          // Format the top result as a chat response
          const topResult = results[0];
          const response = `Based on the Codex article "${topResult.title}": ${topResult.summary || topResult.content.substring(0, 200)}...`;
          this.chatMessages.push({ role: 'assistant', content: response });
        } else {
          this.chatMessages.push({ 
            role: 'assistant', 
            content: 'I couldn\'t find relevant information about that. Try rephrasing your question about Baybayin.' 
          });
        }
        this.chatLoading = false;
      },
      error: (err) => {
        this.chatMessages.push({ 
          role: 'assistant', 
          content: 'Sorry, I encountered an error. Please try again.' 
        });
        this.chatLoading = false;
        console.error('Chat error:', err);
      }
    });
  }

  clearChat() {
    this.chatMessages = [];
  }

  // --- Tag Filter Methods ---
  selectTag(tag: string) {
    if (this.selectedTag === tag) {
      // Deselect tag
      this.selectedTag = null;
      this.filteredArticles = this.articles;
    } else {
      this.selectedTag = tag;
      this.baybayinWikiService.getArticlesByTag(tag).subscribe({
        next: (articles) => {
          this.filteredArticles = articles;
        },
        error: (err) => {
          console.error('Failed to filter by tag:', err);
          this.filteredArticles = this.articles;
        }
      });
    }
  }

  applyKudlit(vowel: 'a' | 'e/i' | 'o/u'): void {
    this.currentVowel = vowel;
    const baseChar = { latin: 'B' };
    const result = this.kudlitMap[vowel];
    this.activeKudlitChar = result.baybayin;
    this.activeLatinChar = baseChar.latin + result.latin;
  }

  // --- Modal State ---
  modalVisible: boolean = false;
  modalChar: string = '';
  modalTitle: string = '';
  modalDesc: string = '';

  openCharModal(char: string, title: string, desc: string): void {
    this.modalChar = char;
    this.modalTitle = title;
    this.modalDesc = desc;
    this.modalVisible = true;
  }

  closeCharModal(): void {
    this.modalVisible = false;
  }

  toggleAccordion(event: Event): void {
    const element = event.currentTarget as HTMLElement;
    const accordionItem = element.closest('.accordion-item');
    if (accordionItem) {
      accordionItem.classList.toggle('active');
    }
  }

  openWikiMenu(): void {
    this.wikiMenuOpen = !this.wikiMenuOpen;
  }

  closeWikiMenu(): void {
    this.wikiMenuOpen = false;
  }

  selectWikiSection(section: string): void {
    this.selectedWikiSection = section;
    this.wikiMenuOpen = false;
    // Optionally, add logic to filter/display content based on section
  }
}

