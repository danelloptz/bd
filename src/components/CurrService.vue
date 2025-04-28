<template>
    <div class="newVisitWrapper">
        <section class="newVisit">
          <!-- Кнопка "Назад" -->
          <svg @click="back" class="backIcon icon" viewBox="0 0 1024 1024" fill="white" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
            <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g>
            <g id="SVGRepo_iconCarrier">
              <path d="M669.6 849.6c8.8 8 22.4 7.2 30.4-1.6s7.2-22.4-1.6-30.4l-309.6-280c-8-7.2-8-17.6 0-24.8l309.6-270.4c8.8-8 9.6-21.6 2.4-30.4-8-8.8-21.6-9.6-30.4-2.4L360.8 480.8c-27.2 24-28 64-0.8 88.8l309.6 280z" fill=""></path>
            </g>
          </svg>

          <!-- Заголовок -->
          <h1>Услуги</h1>
          <span><strong>Дата приезда: </strong>{{ userData.datBegin }}</span>
          <span><strong>Дата отъезда: </strong>{{ userData.datEnt }}</span>
          <span><strong>ФИО клиента: </strong>{{ userData["ФИО_клиента"] }}</span>
          <span><strong>Номер комнаты: </strong>{{ userData["intRoomNumber"] }}</span>
          <span><strong>Стоимость услуг: </strong>{{ userData.fltServiceSum }}</span>

          <table class="table">
            <thead>
              <tr>
                <th>Наименование услуги</th>
                <th>Количество</th>
                <th>Сумма</th>
                <th>Дата оказания</th>
                <th>Стоимость</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(service, index) in services" :key="index">
                <td>{{ service.Наименование_услуги }}</td>
                <td>{{ service.Количество }}</td>
                <td>{{ service.Сумма }}</td>
                <td>{{ service.Дата_оказания }}</td>
                <td>{{ service.Стоимость }}</td>
              </tr>
            </tbody>
          </table>

          <!-- Кнопка "Добавить визит" -->
          <button class="add_btn" @click="addService">Добавить услугу</button>
        </section>
    </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
        userData: null,
        services: [], // Массив для хранения данных об услугах
    };
  },
  async created() {
    this.userData = JSON.parse(localStorage.getItem("curr_user"));
    await this.fetchServices();
  },
  methods: {
    back() {
      this.$router.push('/'); // Возвращаемся на главную страницу
    },
    async fetchServices() {
      try {
        console.log(this.userData);
        const response = await axios.get(`http://127.0.0.1:8000/api/client/services/${this.userData.intClientId}/${this.userData.intVisitId}`);
        this.services = response.data;
      } catch (error) {
        console.error('Ошибка при загрузке данных:', error);
      }
    },
    addService() {
      this.$router.push('/new-service');
    }
  },
};
</script>

<style scoped>
.newVisitWrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100vw;
  background: -webkit-linear-gradient(90deg, #000000,#000040);background: linear-gradient(90deg, #000000,#1a1a84);
}
.newVisit {
background: #020227;
  padding: 40px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  /* width: 50vw; */
  text-align: center;
  display: flex;
  flex-direction: column;
  row-gap: 25px;
  /* align-items: center; */
  position: relative;
}

.backIcon {
    cursor: pointer;
    margin-bottom: 20px;
    position: absolute;
    top: 30px;
    left: 20px;
    width: 40px;
    height: 40px;
}

.row {
  display: flex;
  column-gap: 30px;
  margin-bottom: 15px;
}

.item {
  width: 48%;
}

input {
  width: 300px;
  padding: 8px;
  margin-top: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.add_btn {
  background-color: #3f83e9;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 20px;
}

.add_btn:hover {
  background-color: #2a6ecb;
}

.table {
    max-height: 500px;
    overflow-y: auto;
    background: #020227;
    padding: 25px;
    font-size: 16px;
  }
  td, th {
    padding: 10px;
    cursor: pointer;
    transition: .2s ease-in;
  }
  td:hover {
    background: rgba(255, 255, 255, 0.201);
  }
  span {
    align-self: self-start;
  }
</style>