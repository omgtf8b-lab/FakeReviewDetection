import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:frontend_mobile/services/review_api_service.dart';

void main() {
  test('Loads all review pages and distinguishes fake probability from label confidence', () async {
    final pages = <int>[];
    ReviewApiService.setClientForTesting(MockClient((request) async {
      final page = int.parse(request.url.queryParameters['page']!);
      pages.add(page);
      final items = List.generate(page == 1 ? 100 : 1, (index) => {'id':(page-1)*100+index+1,'product_id':1,'user_id':2,'rating':4,'content':'Review $index',
        'prediction':{'predicted_label':'real','fake_probability':.08,'real_probability':.92,'confidence_score':.92}});
      return http.Response(jsonEncode({'items':items,'total':101,'page':page,'page_size':100}),200);
    }));
    final reviews = await ReviewApiService.getReviewsByProduct(1);
    expect(reviews.length,101);
    expect(pages,[1,2]);
    expect(reviews.first.fakeConfidence,.08);
    expect(reviews.first.prediction!.confidenceScore,.92);
  });
}
