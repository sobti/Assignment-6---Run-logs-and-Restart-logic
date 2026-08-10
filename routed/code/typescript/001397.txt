import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SidebarComponent } from './sidebar/sidebar.component';
import { NavbarComponent } from './navbar/navbar.component';
import { FooterComponent } from './footer/footer.component';
import { RouterModule } from '@angular/router';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { CardInformationComponent } from './card-information/card-information.component';
import { LoaderComponent } from './loader/loader.component';
import { AlertaNoDataComponent } from './alerta-no-data/alerta-no-data.component';

@NgModule({
  imports: [
    CommonModule,
    RouterModule,
    NgbModule
  ],
  declarations: [
    FooterComponent,
    NavbarComponent,
    SidebarComponent,
    CardInformationComponent,
    LoaderComponent,
    AlertaNoDataComponent
  ],
  exports: [
    FooterComponent,
    NavbarComponent,
    SidebarComponent,
    CardInformationComponent,
    LoaderComponent,
    AlertaNoDataComponent
  ]
})
export class ComponentsModule { }
