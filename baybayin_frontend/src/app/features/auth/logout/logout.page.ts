import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthenticationService } from 'src/app/core/services/authentication.service';

@Component({
  selector: 'app-logout',
  template: '<p>Logging out...</p>',
  standalone: false
})
export class LogoutPage implements OnInit {

  constructor(
    private authenticationService: AuthenticationService,
    private router: Router
  ) { }

  async ngOnInit() {
    await this.authenticationService.logout()

    this.router.navigate(['/login'], { replaceUrl: true })
  }

}
