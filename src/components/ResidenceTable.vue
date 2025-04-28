<template>
  <div class="wrapper">
    <div class="table">
      <h1>Проживание</h1>
      <table border="1">
        <thead>
          <tr>
            <th>Дата приезда</th>
            <th>Дата отъезда</th>
            <th>ФИО клиента</th>
            <th>Номер комнаты</th>
            <th>Этаж</th>
            <th>Стоимость услуг</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in residenceData" :key="index" @click="openService(row)">
            <td>{{ row['datBegin'] }}</td>
            <td>{{ row['datEnt'] }}</td>
            <td>{{ row['ФИО_клиента'] }}</td>
            <td>{{ row['intRoomNumber'] }}</td>
            <td>{{ row['Этаж'] }}</td>
            <td>{{ row['fltServiceSum'] }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <button class="add_btn" @click="addVisit">Добавить визит</button>

  </div>
    
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      residenceData: [],
    };
  },
  mounted() {
    this.fetchResidenceData();
  },
  methods: {
    async fetchResidenceData() {
      try {
        const response = await axios.get('http://127.0.0.1:8000/api/residence');
        this.residenceData = response.data;
      } catch (error) {
        console.error('Ошибка при получении данных:', error);
      }
    },
    addVisit() {
      this.$router.push('/new-visit');
    },
    openService(user) {
      localStorage.setItem('curr_user', JSON.stringify(user));
      this.$router.push('/service');
    }
  }
};
</script>

<style scoped>
  .wrapper {
    width: 100vw;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    background: -webkit-linear-gradient(90deg, #000000,#000040);background: linear-gradient(90deg, #000000,#1a1a84);
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
  h1 {
    text-align: center;
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