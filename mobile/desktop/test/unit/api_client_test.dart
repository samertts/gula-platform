import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:dio/dio.dart';
import '../../lib/core/api/api_client.dart';
import '../../lib/core/api/api_endpoints.dart';
import '../../lib/core/api/api_exceptions.dart';

import 'api_client_test.mocks.dart';

@GenerateMocks([Dio])
void main() {
  late MockDio mockDio;
  late ApiClient apiClient;

  setUp(() {
    mockDio = MockDio();
    apiClient = ApiClient(
      baseUrl: 'https://api.gula-platform.org/api/v1',
      dio: mockDio,
    );
  });

  group('ApiClient', () {
    test('get returns data on success', () async {
      when(mockDio.get(any)).thenAnswer((_) async => Response(
        requestOptions: RequestOptions(path: '/test'),
        data: {'key': 'value'},
        statusCode: 200,
      ));

      final result = await apiClient.get('/test');
      expect(result, {'key': 'value'});
    });

    test('get throws NotFoundException on 404', () async {
      when(mockDio.get(any)).thenThrow(DioException(
        requestOptions: RequestOptions(path: '/test'),
        response: Response(requestOptions: RequestOptions(path: '/test'), statusCode: 404, data: {'detail': 'Not found'}),
        type: DioExceptionType.badResponse,
      ));

      expect(() => apiClient.get('/test'), throwsA(isA<NotFoundException>()));
    });

    test('post returns data on success', () async {
      when(mockDio.post(any, data: anyNamed('data'))).thenAnswer((_) async => Response(
        requestOptions: RequestOptions(path: '/test'),
        data: {'id': '1'},
        statusCode: 201,
      ));

      final result = await apiClient.post('/test', data: {'name': 'test'});
      expect(result, {'id': '1'});
    });

    test('put updates successfully', () async {
      when(mockDio.put(any, data: anyNamed('data'))).thenAnswer((_) async => Response(
        requestOptions: RequestOptions(path: '/test/1'),
        statusCode: 200,
      ));

      await apiClient.put('/test/1', data: {'name': 'updated'});
    });

    test('delete removes resource', () async {
      when(mockDio.delete(any)).thenAnswer((_) async => Response(
        requestOptions: RequestOptions(path: '/test/1'),
        statusCode: 204,
      ));

      await apiClient.delete('/test/1');
    });

    test('download saves file', () async {
      when(mockDio.download(any, any)).thenAnswer((_) async => Response(
        requestOptions: RequestOptions(path: '/report'),
        statusCode: 200,
      ));

      await apiClient.download('/report', '/tmp/report.pdf');
    });
  });
}
