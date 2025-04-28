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
        <h1>Добавить услугу</h1>

        <span><strong>ФИО клиента: </strong>{{ userData["ФИО_клиента"] }}</span>
        <span><strong>Дата приезда: </strong>{{ userData.datBegin }}</span>
        <span><strong>Дата отъезда: </strong>{{ userData.datEnt }}</span>

        <!-- Выпадающий список типов услуг -->
        

        <!-- Поле для количества услуг -->
        <div class="row">
          <div class="form-group">
            <label for="serviceType">Наименование услуги:</label>
            <select id="serviceType" v-model="selectedService" class="form-control">
              <option v-for="service in services" :key="service.id" :value="service">
                {{ service.name }} ({{ service.price }} руб.)
              </option>
            </select>
          </div>
          <div class="form-group">
            <label for="quantity">Количество:</label>
            <input type="number" id="quantity" v-model="quantity" min="1" class="form-control" />
          </div>
        </div>
        
        <div class="row">
          <div class="form-group">
            <label for="totalSum">Сумма:</label>
            <input type="text" id="totalSum" :value="totalSum" readonly class="form-control" />
          </div>

          <!-- Поле для даты оказания услуги -->
          <div class="form-group">
            <label for="serviceDate">Дата оказания:</label>
            <input type="date" id="serviceDate" v-model="serviceDate" class="form-control" />
          </div>
        </div>

        <!-- Кнопка "Добавить услугу" -->
        <button class="add_btn" @click="addService">Добавить услугу</button>
      </section>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      userData: null, // Данные о текущем клиенте
      services: [],   // Массив типов услуг
      selectedService: null, // Выбранный тип услуги
      quantity: 1,    // Количество услуг
      serviceDate: "", // Дата оказания услуги
    };
  },
  async created() {
    // Загружаем данные о текущем клиенте из localStorage
    this.userData = JSON.parse(localStorage.getItem("curr_user"));
    if (this.userData) {
      await this.fetchServiceTypes();
    } else {
      console.error("Данные о клиенте не найдены в localStorage.");
    }
  },
  computed: {
    totalSum() {
      // Вычисляем сумму на основе выбранного типа услуги и количества
      if (this.selectedService && this.quantity) {
        return (this.selectedService.price * this.quantity).toFixed(2);
      }
      return 0;
    },
  },
  methods: {
    back() {
      this.$router.push('/service'); // Возвращаемся на главную страницу
    },
    async fetchServiceTypes() {
      try {
        const response = await axios.get('http://127.0.0.1:8000/api/service/types');
        this.services = response.data;
      } catch (error) {
        console.error('Ошибка при загрузке данных:', error);
      }
    },
    async addService() {
      try {
        // Проверяем, что все обязательные поля заполнены
        if (!this.selectedService || !this.quantity || !this.serviceDate) {
          alert("Пожалуйста, заполните все поля.");
          return;
        }

        // Преобразуем даты в объекты Date для сравнения
        const selectedDate = new Date(this.serviceDate);
        const beginDate = new Date(this.userData.datBegin);
        const endDate = new Date(this.userData.datEnt);

        // Проверяем, что выбранная дата попадает в период проживания
        if (selectedDate < beginDate || selectedDate > endDate) {
          alert("Выбранная дата оказания услуги не попадает в период проживания.");
          return;
        }

        // Отправляем данные на бэкенд
        const response = await axios.post('http://127.0.0.1:8000/api/service/add_service', {
          service_type_id: this.selectedService.id,
          visit_id: this.userData.intVisitId, // Предполагается, что ID визита хранится в userData
          service_count: this.quantity,
          service_sum: parseFloat(this.totalSum),
          service_date: this.serviceDate,
        });

        console.log(response.data);
        alert("Услуга успешно добавлена!");
      } catch (error) {
        console.error('Ошибка при отправке данных:', error);
        alert("Произошла ошибка при добавлении услуги.");
      }
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

h1 {
  align-self: center;
}
span {
  align-self: self-start;
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

.form-group {
  margin-bottom: 15px;
  text-align: left;
  display: flex;
  flex-direction: column;
}

label {
  font-weight: bold;
}

input, select {
  max-width: 500px;
  width: 20vw;
  padding: 8px;
  margin-top: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;

}
</style>