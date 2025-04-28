<template>
    <div class="wrapper">
        <div class="main-form">
            <h1>Главная форма</h1>
        
            <!-- Кнопка для вызова формы "Проживание" -->
            <button class="btn" @click="openAccommodationForm">Проживание</button>
        
            <!-- Кнопка для вызова первого отчета ("Услуги") -->
            <button class="btn" @click="generateServicesReport">Отчет: Услуги</button>
        
            <!-- Кнопка для вызова второго отчета ("Клиенты") -->
            <button class="btn" @click="generateClientsReport">Отчет: Клиенты</button>
        
            <!-- Форма для вызова третьего отчета ("Комнаты") -->
            <div class="room-report-form">
                <label for="roomNumber">Выберите номер комнаты:</label>
                <select id="roomNumber" v-model="selectedRoom" class="form-control">
                <option v-for="room in rooms" :key="room.intRoomNumber" :value="room.intRoomNumber">
                    {{ room.intRoomNumber }} (Этаж: {{ room.intFlor }}, Цена: {{ room.fltRoomPrice }} руб.)
                </option>
                </select>
                <button class="btn" @click="generateRoomsReport">Отчет: Комнаты</button>
            </div>
        </div>
    </div>
    
  </template>
  
  <script>
  import axios from 'axios';
  
  export default {
    data() {
      return {
        rooms: [], // Список комнат
        selectedRoom: null, // Выбранный номер комнаты
      };
    },
    async created() {
      try {
        // Загружаем список комнат из базы данных
        const response = await axios.get('http://127.0.0.1:8000/api/rooms');
        this.rooms = response.data;
      } catch (error) {
        console.error('Ошибка при загрузке списка комнат:', error);
      }
    //   await this.makeTrigger();
    },
    methods: {
      openAccommodationForm() {
        // Переход к форме "Проживание"
        this.$router.push('/');
      },
      async generateServicesReport() {
        // Генерация отчета "Услуги"
        window.open('http://127.0.0.1:8000/api/report/services', '_blank');
      },
      async generateClientsReport() {
        // Генерация отчета "Клиенты"
        window.open('http://127.0.0.1:8000/api/report/clients', '_blank');
      },
      async generateRoomsReport() {
        if (!this.selectedRoom) {
          alert('Пожалуйста, выберите номер комнаты.');
          return;
        }
        // Генерация отчета "Комнаты" с выбранным номером комнаты
        window.open(`http://127.0.0.1:8000/api/report/rooms/${this.selectedRoom}`, '_blank');
      },
    //   async makeTrigger() {
    //     const resp = await axios.post('http://127.0.0.1:8000/api/trigger/create');
    //     console.log(resp);
    //   }
    },
  };
  </script>
  
  <style scoped>
  .wrapper {
    width: 100%;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    background: -webkit-linear-gradient(90deg, #000000,#000040);background: linear-gradient(90deg, #000000,#1a1a84);

  }
  .main-form {
    text-align: center;
    margin-top: 50px;
    background: #020227;
    padding: 25px;
    border-radius: 10px;
  }
  
  .btn {
    background-color: #3f83e9;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    margin: 10px;
  }
  
  .btn:hover {
    background-color: #2a6ecb;
  }
  
  .room-report-form {
    margin-top: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  .form-control {
    padding: 8px;
    margin-right: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
  select {
    width: fit-content;
  }
  </style>