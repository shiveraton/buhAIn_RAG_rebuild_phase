import { Injectable } from '@angular/core';
import { environment } from 'src/environments/environment';
import { initializeApp } from 'firebase/app';
import { getFirestore, doc, setDoc, getDoc, getDocs, collection } from 'firebase/firestore';
@Injectable({
  providedIn: 'root'
})
export class ImageClassificationSystemService {
  private app =   initializeApp(environment.firebaseConfig)
  private db = getFirestore(this.app)

  constructor() { 
  }

  public async storeModelPipelineAndResult(
    
  ){

  }

  public async getModelPipelineMethods(){
    
    const pipelineMethods = collection(this.db, 'model_pipeline_methods')
    const pipelineMethodsSnap = await getDocs(pipelineMethods);
    if(pipelineMethodsSnap.empty){
        throw { code: 'methods-empty', message: 'Model Pipeline Methods is empty!' } 
    }

    const methods = pipelineMethodsSnap.docs.map(doc => {
      const data = doc.data();
      return {
        module_name: data['module_name'],
        complete_name: data['complete_name'],
        category_name: data['category']
      };
    });

    return methods;
  }
}
