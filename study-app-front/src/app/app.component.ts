import { Component, OnInit,inject } from '@angular/core';
import { environment } from 'src/environments/environment';
import { Observable, catchError, map, throwError } from 'rxjs';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  private env = environment as any;
  private httpClient: HttpClient = inject(HttpClient);
  public title = 'study-app-front';

  public organizationNames:string[] = []

  ngOnInit(): void {
    this.fetchOrganizations().subscribe(data => {
      this.organizationNames = data
    })
  }

  private fetchOrganizations(): Observable<string[]> {
    const reqPath = `${this.env.apiHost}/organizations`;

    return this.httpClient.get(reqPath).pipe(
      map((res: any) => {
        return res;
      })
    );
  }
}
