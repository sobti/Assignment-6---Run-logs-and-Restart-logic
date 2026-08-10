import { Routes, RouterModule } from '@angular/router';

import { ProfileComponent } from './profile.component';
import { ProfileTableComponent } from './profileManage/profileTable.component';
import { ProfileDataComponent } from './profileManage/profileData.component';

const routes: Routes = [
  {
    path: '',
    component: ProfileComponent,
    children: [
      { path: 'profile-manager', component: ProfileDataComponent }
    ]
  }
];

export const routing = RouterModule.forChild(routes);
