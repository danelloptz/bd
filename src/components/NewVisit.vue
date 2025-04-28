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
          <h1>Новый визит</h1>

          <!-- Дата приезда и номер комнаты -->
          <div class="row">
              <div class="item">
                  <h2>Дата приезда:</h2>
                  <input placeholder="Дата приезда" type="date" v-model="datBegin">
              </div>
              <div class="item">
                  <h2>Дата приезда:</h2>
                  <input placeholder="Дата отъезда" type="date" v-model="datEnd">
              </div>
              
          </div>

          <!-- ФИО клиента -->
          <div class="row" style="justify-content: center;">
            <div class="item">
                  <h2>Номер комнаты:</h2>
                  <input placeholder="Номер комнаты" type="number" v-model="roomNumber">
              </div>
              <div class="item" style="width: 80%;">
                  <h2 style="text-align: center;">ФИО клиента:</h2>
                  <input placeholder="ФИО клиента" type="text" v-model="client">
              </div>
          </div>

          <!-- Кнопка "Добавить визит" -->
          <button class="add_btn" @click="addVisit">Добавить визит</button>
        </section>
    </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      datBegin: "", // Дата приезда
      datEnd: "",   // Дата отъезда
      roomNumber: null, // Номер комнаты
      floorNumber: null, // Этаж
      client: "",   // ФИО клиента
      passportNumber: "" // Номер паспорта
    };
  },
  methods: {
    back() {
      this.$router.push('/'); // Возвращаемся на главную страницу
    },
    async addVisit() {
      try {
        // Проверяем, что все обязательные поля заполнены
        if (!this.datBegin || !this.datEnd || !this.roomNumber || !this.client) {
          alert("Пожалуйста, заполните все поля.");
          return;
        }

        // Отправляем POST-запрос на сервер
        const response = await axios.post('http://127.0.0.1:8000/api/visit/add_visit', {
          datBegin: this.datBegin,
          datEnt: this.datEnd,
          ФИО_клиента: this.client,
          Номер_комнаты: parseInt(this.roomNumber),
        });

        console.log(response);
        alert("Визит успешно добавлен!");
      } catch (error) {
        console.error('Ошибка при отправке данных:', error);
        alert("Произошла ошибка при добавлении визита.");
      }
    }
  }
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
  align-items: center;
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
</style>