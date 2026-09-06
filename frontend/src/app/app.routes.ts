import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'messages', pathMatch: 'full' },
  {
    path: 'messages',
    loadComponent: () => import('./features/queue/queue.component').then(m => m.QueueComponent)
  },
  {
    path: 'messages/:id',
    loadComponent: () => import('./features/detail/detail.component').then(m => m.DetailComponent)
  },
  {
    path: 'batch',
    loadComponent: () => import('./features/batch/batch.component').then(m => m.BatchComponent)
  },
  {
    path: 'literature',
    loadComponent: () => import('./features/literature/literature.component').then(m => m.LiteratureComponent)
  },
  { path: '**', redirectTo: 'messages' }
];
