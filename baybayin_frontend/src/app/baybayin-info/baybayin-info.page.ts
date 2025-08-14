import { Component, OnInit } from '@angular/core';
import { AlertController } from '@ionic/angular';
import { BaybayinWikiService, WikiArticle } from './baybayin-wiki.service';

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

  // --- Kudlit Playground Properties ---
  activeKudlitChar: string = 'ᜊ';
  activeLatinChar: string = 'Ba';
  currentVowel: 'a' | 'e/i' | 'o/u' = 'a';
  private kudlitMap = {
    'a': { baybayin: 'ᜊ', latin: 'a' },
    'e/i': { baybayin: 'ᜊᜒ', latin: 'i' },
    'o/u': { baybayin: 'ᜊᜓ', latin: 'u' }
  };

  constructor(
    private baybayinWikiService: BaybayinWikiService,
    private alertController: AlertController
  ) {}

  ngOnInit() {
    this.baybayinWikiService.getBaybayinArticles().subscribe({
      next: (data) => {
        this.articles = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load Baybayin articles.';
        this.loading = false;
      }
    });
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
}
