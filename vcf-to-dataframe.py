## VCF to Spark DataFrame using Glow

from pyspark.sql.functions import *
import glow
spark = glow.register(spark)

## Define input path(s) to VCF file(s)
input_paths = ['']

## Read VCF file(s) into a Spark DataFrame
vcf_df = spark.read.format("vcf") \
              .option("flattenInfoFields", True) \
              .option("includeSampleIds", True) \
              .load(input_paths) \
              .select("*", glow.expand_struct(glow.call_summary_stats("genotypes"))) \
              .withColumn("annotation", to_json(col("INFO_ANN")).cast('string')) \
              .withColumn("names", col("names").cast('string')) \
              .select("INFO_SAMPLE", "contigName", "start", "end", "names", "referenceAllele", "alternateAlleles", "annotation")

# display(vcf_df)

## Split multiallelic variants into multiple rows
vcf_df_split = glow.transform("split_multiallelics", vcf_df) \
                   .withColumn("alternateAlleles", explode(col("alternateAlleles"))) \
                   .withColumnRenamed("INFO_SAMPLE", "sample_id") \
                   .withColumn("annotation", regexp_replace("annotation", ',', '|')) \
                   .drop("splitFromMultiAllelic", "INFO_OLD_MULTIALLELIC")
                #    .withColumn("start", col("start").cast('string')) \
                #    .withColumn("end", col("end").cast('string')) \
# display(vcf_df_split)

## Write Spark DataFrame to Delta Lake
output_path = ''

vcf_df_split.coalesce(1).write.options(header='True', delimiter='\t').mode("overwrite").csv(output_path)