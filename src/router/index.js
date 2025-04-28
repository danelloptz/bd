import { createRouter, createWebHistory } from 'vue-router';
import NewVisit from '@/components/NewVisit.vue';
import CurrService from '@/components/CurrService.vue';
import ResidenceTable from '@/components/ResidenceTable.vue';
import NewService from '@/components/NewService.vue';
import MainForm from '@/components/MainForm.vue';

const routes = [
    { path: '/', component: ResidenceTable },
    { path: '/new-visit', component: NewVisit },
    { path: '/service', component: CurrService },
    { path: '/new-service', component: NewService },
    { path: '/main', component: MainForm },
];

const router = createRouter({
    history: createWebHistory(),
    // history: createWebHistory(process.env.BASE_URL),
    routes
});

export default router;
