import { Component, OnInit } from '@angular/core';
import { AuthService } from 'src/app/services/auth.service';
import { UserAuth } from 'src/app/interfaces/UserAuth';
import { FormGroup, FormControl } from '@angular/forms';
import { RegisterForm } from 'src/app/interfaces/RegisterForm';
import { FirebaseService } from 'src/app/services/firebase.service';

@Component({
  selector: 'app-complete-data',
  templateUrl: './complete-data.component.html',
  styleUrls: ['./complete-data.component.scss'],
})
export class CompleteDataComponent implements OnInit 
{
  // !user.email || !user.phone || user.addresses.length == 0

  // Usuario actualmente logueado.
  public user: UserAuth;

  // Inidica si el código postal introducido es aceptado.
  public isValidZip: boolean;

  // Formulario con los datos de registro.
  public completeDataForm = new FormGroup({
    email: new FormControl(''),
    phone: new FormControl(''),
    street: new FormControl(''),
    street_optional: new FormControl(''),
    zip: new FormControl(''),
  });

  constructor(
    private authService: AuthService,
    private firebaseService: FirebaseService
  ) 
  { 
    this.user = this.authService.user;
    console.log('el usuario autenticado es: ');
    console.log(this.user);
    this.isValidZip = false;
  }

  ngOnInit() 
  {
    this.user = this.authService.user;
  }

  /**
   * Completa la información del usuario logueado y pide al servicio 
   * que registre este cambio en la base de datos.
   */
  completeUserData()
  {
    let userComplete = {
      uid: this.user.uid,
      names: this.user.names,
      surnames: this.user.surnames,
      addresses: (this.user.addresses.length == 0) ? [{ street: this.completeDataForm.value.street, 
                                                        street_optional: this.completeDataForm.value.street_optional,
                                                        zip: this.completeDataForm.value.zip
                                                     }] : this.user.addresses,      
  
      email: (!this.user.email) ? this.completeDataForm.value.email : this.user.email,
      phone: (!this.user.phone) ? this.completeDataForm.value.phone : this.user.phone,
    };

    this.firebaseService.completeUserData(userComplete);
    console.log(this.completeDataForm.value);
  }

  /**
   * Verifica que el código postal introducido por el usuario sea válido.
  */
  verifyZip()
  {
    const enterZip = <string>this.completeDataForm.controls['zip'].value;
    this.isValidZip = this.authService.validateZipCode(enterZip);
  }

}
